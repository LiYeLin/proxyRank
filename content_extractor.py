# content_extractor.py
import logging
import re  # 导入 re 用于更灵活的清理
from datetime import datetime
from urllib.parse import urljoin, unquote

from bs4 import BeautifulSoup  # 导入 Comment 用于移除注释

from models.articleInfo import articleInfo
from utils.url_util import is_valid_url

logger = logging.getLogger(__name__)

def extract_content_bs(html_content: str, article_url: str) -> articleInfo | None:
    """
    使用 BeautifulSoup 从 HTML 中提取文章信息。
    已根据提供的 HTML 样本调整选择器。
    """
    try:
        # 预处理：移除 HTML 注释，因为示例 HTML 开头有注释
        html_content_no_comments = re.sub(r'', '', html_content, flags=re.DOTALL)
        soup = BeautifulSoup(html_content_no_comments, 'html.parser')

        # --- 提取标题 ---
        # 查找 h1.post-title 或 title 标签
        title_tag = soup.find('h1', class_='post-title')
        if not title_tag:
            # 有些页面可能把标题放在 <title hidden> 中
            hidden_title = soup.find('title', hidden=True)
            if hidden_title:
                 title_text_raw = hidden_title.get_text(strip=True)
            else: # 最后尝试普通的 <title>
                 title_tag_fallback = soup.find('title')
                 title_text_raw = title_tag_fallback.get_text(strip=True) if title_tag_fallback else "未知标题"
        else:
             title_text_raw = title_tag.get_text(strip=True)

        # 清理标题 (移除可能的网站后缀)
        article_title = title_text_raw.split(' - DuyaoSS')[0].strip()
        # 进一步清理，移除前后多余字符
        article_title = article_title.strip()


        # --- 提取发布时间 ---
        # 优先使用 meta 标签 property="article:published_time"
        time_tag = soup.find('meta', property='article:published_time')
        article_datetime_str = None
        if time_tag:
            article_datetime_str = time_tag.get('content')
        else:
            # 备选：查找 time 标签
            time_tag_fallback = soup.find('time', datetime=True)
            if time_tag_fallback:
                article_datetime_str = time_tag_fallback['datetime']
            else:
                 logger.warning(f"未找到文章 '{article_title}' 的精确发布时间标签。")


        article_datetime = datetime.now() # 默认当前时间
        if article_datetime_str:
            try:
                # 尝试解析 ISO 格式带时区
                # 移除可能的毫秒部分 (BeautifulSoup 可能不处理)
                if '.' in article_datetime_str and ('+' in article_datetime_str or 'Z' in article_datetime_str):
                     time_part, tz_part = article_datetime_str.split('+', 1) if '+' in article_datetime_str else article_datetime_str.split('Z', 1)
                     if '.' in time_part:
                          time_part = time_part.split('.')[0]
                     article_datetime_str = f"{time_part}+{tz_part}" if '+' in article_datetime_str else f"{time_part}Z"

                # 替换 Z 为 +00:00 以便 fromisoformat 处理
                dt_str_iso = article_datetime_str.replace('Z', '+00:00')
                # 移除可能存在的秒后的小数点部分（如果上面处理不完整）
                if '.' in dt_str_iso:
                    match = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.?\d*([+-]\d{2}:\d{2})", dt_str_iso)
                    if match:
                        dt_str_iso = match.group(1) + match.group(2)

                article_datetime = datetime.fromisoformat(dt_str_iso)

            except ValueError as e:
                logger.warning(f"无法解析文章 '{article_title}' 的日期时间字符串 '{article_datetime_str}' (原始: '{time_tag.get('content') if time_tag else 'N/A'}'): {e}. 使用当前时间替代.")
        else:
             logger.info(f"未找到文章 '{article_title}' 的发布时间，使用当前时间。") # 改为 Info 级别


        # --- 提取文章主内容区域 ---
        # !! 修改后的选择器，优先查找 div.articleBody !!
        content_div = soup.find('div', class_='articleBody') # 主要目标
        if not content_div:
             # 备选：查找 <article class="post yue"> 或 <article class="post">
             content_div = soup.find('article', class_=lambda c: c and ('post' in c.split() or 'yue' in c.split()))
        if not content_div:
             # 原始备选方案
            content_div = soup.find('article', class_='post-content') or \
                          soup.find('div', class_='entry-content') or \
                          soup.find('div', id='article-content')

        if not content_div:
            logger.error(f"无法在 URL {article_url} 中找到主要内容容器。检查选择器或页面结构。")
            return None
        else:
             logger.info(f"成功找到主要内容容器，标签: <{content_div.name} class='{' '.join(content_div.get('class', []))}' id='{content_div.get('id', '')}'>")


        # --- 提取纯文本内容 ---
        # get_text() 会提取所有子标签的文本
        article_text = content_div.get_text(separator='\n', strip=True)

        # --- 提取图片链接 ---
        article_images = []
        # 在找到的 content_div 内部查找所有 img 标签
        for img_tag in content_div.find_all('img'):
            # 优先尝试 'data-src' (用于懒加载)，然后是 'src'
            src = img_tag.get('data-src') or img_tag.get('src')
            if src:
                 src = src.strip()
                 # 移除 URL 末尾可能存在的 #vwid=...&vhei=... 部分
                 src_cleaned = src.split('#')[0]
                 # URL 解码，处理像 %3A 这样的字符
                 src_decoded = unquote(src_cleaned)

                 # 转换为绝对 URL
                 absolute_src = urljoin(article_url, src_decoded)

                 if is_valid_url(absolute_src):
                     article_images.append(absolute_src)
                 else:
                     logger.warning(f"在 {article_url} 发现无效或转换后仍无效的图片链接: '{absolute_src}' (原始: '{src}')")
            # else: # 忽略没有 src 或 data-src 的 img 标签
            #     logger.debug(f"在 {article_url} 发现缺少 src/data-src 的 img 标签: {img_tag}")


        return articleInfo(
            articleTitle=article_title,
            articleText=article_text,
            articleUrl=article_url,
            articleImages=list(set(article_images)), # 去重
            articleDateTime=article_datetime,
            htmlContent=html_content # 保留原始 HTML 可能有用
        )

    except Exception as e:
        logger.error(f"使用 BeautifulSoup 解析 URL {article_url} 时出错: {e}", exc_info=True)
        return None
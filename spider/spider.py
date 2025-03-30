import logging
from datetime import datetime
from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from models.articleInfo import articleInfo
from utils.RetrySession import RetrySession
from utils.url_util import is_valid_url

APP_LOGGER_NAME = "spider"
logger = logging.getLogger(APP_LOGGER_NAME)

req = RetrySession(total_retries=5)


def get_article_url_list(base_url):
    articles = []
    page = 1
    while True:
        # 构造分页 URL（如 https://example.com/page/2/）
        url = urljoin(base_url, f"page/{page}/") if page >= 1 else base_url
        try:
            response = req.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching URL: {e}")
            break
        if not has_article(response.text):
            logger.info("已经读取全部文章")
            break
        soup = BeautifulSoup(response.text, 'html.parser')
        # 定位所有文章条目
        for item in soup.select('ul#masonry > li.masonry-item > a[href]'):
            linkInfo = item.get('href')
            if not linkInfo: continue
            # if item.get()
            # 提取基础信息
            title_elem = item.select_one('h1.title').text.strip()
            date_object = datetime.strptime(item.select_one('time').text, '%b %d, %Y')
            # 将结果放在articleInfo对象中 并且构建列表
            info = articleInfo(articleTitle=title_elem, articleUrl=linkInfo, articleText=None, articleImages=[],
                               htmlContent=None, articleDateTime=date_object)
            articles.append(info)
        logger.info(f"已抓取第 {page} 页，共 {len(articles)} 篇文章")
        page += 1
        sleep(2)

    return articles


def has_article(html_content):
    """
    判断 HTML 内容是否包含文章（基于是否存在 <li id="masonry-item"> 标签）。

    Args:
        html_content: 包含 HTML 内容的字符串。

    Returns:
        True 如果包含文章，False 否则。
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    masonry_ul = soup.find('ul', id='masonry')
    if masonry_ul:
        list_items = masonry_ul.find_all('li', class_='masonry-item')
        return len(list_items) > 0
    return False


def get_speed_test_info(articleUrl, debugHtml=None):
    if debugHtml is not None:
        html = debugHtml
    else:
        try:
            response = req.get(articleUrl)
            response.raise_for_status()  # Raise an exception for bad status codes
            html = response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return []

    soup = BeautifulSoup(html, 'html.parser')
    post_section = soup.find('section', {'id': 'post'})
    if post_section:
        imagesNode = post_section.find_all('img')
        images = []
        for img in imagesNode:
            src_url = img.get('src') if img.get('src') else img.get('data-src')
            if is_valid_url(src_url):
                images.append(src_url)
        result = [src for src in images if src]
        logger.info("url为{}的文章中共找到图片{}张".format(articleUrl, len(result)))
        return result
    else:
        return []


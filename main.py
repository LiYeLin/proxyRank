# main.py
import logging
import sqlite3
from datetime import datetime
from typing import List
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests  # 导入 requests 以便捕获其异常
from bs4 import BeautifulSoup  # 需要导入以获取列表页信息

import config
from config import (
    TARGET_BLOG_BASE_URL, ARTICLE_LIST_URL, REQUEST_HEADERS, LOG_FILE, DATABASE_NAME  # 如果需要保存图片，则需要此配置
)
from content_extractor import extract_content_bs
from converter import ocr_convert_to_record
from db import sr_merchant_dao, sr_node_dao, ssr_speed_test_record_dao
from db.db_connection import create_tables
from image_downloader import download_image, save_image  # 仅下载 bytes
from llm_interface import extract_info_llm, extract_info_from_image
from models import articleInfo
from score_gemini import evaluate_merchants
from utils.RetrySession import RetrySession
from utils.logger_config import setup_logging

# --- 全局日志配置 ---
logger = setup_logging(log_level=logging.INFO, log_file=LOG_FILE)

# --- 全局会话 ---
retry_session = RetrySession()


def get_article_urls_from_all_page(page_url_idx: str) -> List[str]:
    all_article_urls = []
    #     调用get_article_urls_from_one_page方法 直到返回空数组停止
    idx = 1
    while True:
        urls = get_article_urls_from_one_page(page_url_idx + str(idx) + '/')
        idx += 1
        if not urls:
            break
        all_article_urls.extend(urls)
    logger.info(f"共找到 {len(all_article_urls)} 个唯一文章链接。")
    return all_article_urls


def get_article_urls_from_one_page(page_url: str) -> List[str]:
    """
    从列表页面提取文章链接。
    !! 需要根据目标网站列表页的 HTML 结构定制 !!
    """
    urls = []
    try:
        logger.info(f"正在从列表页获取文章链接: {page_url}")
        response = retry_session.get(page_url, headers=REQUEST_HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # !! 查找包含文章链接的元素，根据实际情况修改选择器 !!
        # 示例：查找所有 class="post-title" 下的 <a> 标签
        # 在 duyaoss.com 例子中，文章链接在 <h2 class="archive-title"> 下的 a 标签
        link_elements = soup.select('ul#masonry > li.masonry-item > a[href]')  # CSS 选择器

        if not link_elements:
            # 尝试其他可能的选择器
            link_elements = soup.select('article h3 a') or soup.select('.post-item a')

        if not link_elements:
            logger.warning(f"在页面 {page_url} 未找到匹配的文章链接元素。请检查选择器。")
            return []

        for link in link_elements:
            href = link.get('href')
            if href:
                # 转换为绝对 URL
                # 如果是 http:// 或 https:// 开头，则直接使用
                if href.startswith(('http://', 'https://')):
                    full_url = href
                else:
                    # 否则，使用 TARGET_BLOG_BASE_URL 转换为绝对 URL
                    full_url = urljoin(TARGET_BLOG_BASE_URL, href)
                # 简单的检查，避免非文章链接 (例如分类、标签链接)
                if urlparse(full_url).path.startswith('/archives/'):  # 根据实际 URL 结构判断
                    urls.append(full_url)

        unique_urls = list(set(urls))
        logger.info(f"从 {page_url} 找到 {len(unique_urls)} 个唯一文章链接。")
        return unique_urls

    except requests.exceptions.RequestException as e:
        logger.exception(f"获取文章列表页面 {page_url} 失败: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.exception(f"解析文章列表页面 {page_url} 时出错: {e}", exc_info=True)
        return []


def extract_and_save_node_and_record(image_url: str, merchant_id: int, merchant_name: str, article_info: articleInfo):
    """
    处理图片并保存节点和测速记录。
    """
    processed_cnt = 0
    # 1. 下载图片
    image_bytes = download_image(image_url, retry_session)
    if not image_bytes:
        raise ValueError("无法下载图片。")
    pic_info = save_image(image_bytes=image_bytes, merchant_name=merchant_name, original_url=image_url)
    img_url = pic_info.get("url")
    logger.info(f"1. 图片下载成功{image_url}")
    # 2. 从图片中提取表格数据
    try:
        logger.info(f"2. 从图片 {image_url} 中提取表格数据。")
        speed_test_record_result = extract_info_from_image(pic_info, merchant_id)
    except ValueError as e:
        logger.error(f"[{merchant_name}]从图片 {img_url} 解析出 OCR 表格数据时出错: 数据问题{e}")
        raise e
    except Exception as e:
        logger.exception(f"[{merchant_name}]从图片 {img_url} 解析出 OCR 表格数据时出错:未知问题 {e}")
        raise e
    if not speed_test_record_result:
        logger.warning(f"[{merchant_name}]未能从图片 {img_url} 解析出 OCR 表格数据。")
        raise ValueError("未能从图片提取表格数据。")
    logger.info(f"2.从[{merchant_name}]图片 {img_url} 解析出ocr数据{len(speed_test_record_result)}条")
    speed_test_record_list = speed_test_record_result.get("test_record_list", [])
    test_time = speed_test_record_result.get("test_time") or article_info.articleDateTime

    # 3. 解析 OCR 结果并存入数据库
    for ocr_record in speed_test_record_list:
        try:
            # 3.1 数据处理
            convert_dict = ocr_convert_to_record(ocr_record, merchant_id, test_time, merchant_name, pic_info)
            sr_node = convert_dict[0]
            # 转换成SSRSpeedTestRecord类型
            sr_record = convert_dict[1]

            # 3.2-- 获取或创建节点记录 --
            node = sr_node_dao.find_or_create_node(sr_node)  # 需要在 sr_node_dao 添加此函数
            if not node or not node.node_id:
                logger.error(
                    f"[{merchant_name}]无法为节点 '{sr_node}' (来自机场 '{merchant_name}') 创建或找到数据库记录。")
                continue
            sr_record.node_id = node.node_id
            record = ssr_speed_test_record_dao.query_record_by_mid_nid_pid(merchant_id, node.node_id,
                                                                           pic_info.get("pic_id"))
            if record:
                logger.info(f"[{merchant_name}]已存在相同测速记录，pass。")
                continue
            # 3.3-- 插入测速记录
            ssr_speed_test_record_dao.create_record(sr_record)
            processed_cnt += 1
        except Exception as e:
            logger.exception(f"[{merchant_name}]处理图片 {img_url} 时出错: {e}")
            continue
        logger.info(f"3. [{merchant_name}]成功处理图片 {len(article_info.articleImages)}张，共存储{processed_cnt} 记录。")


def process_article(article_url: str):
    """处理单篇文章：提取、OCR、存储"""
    logger.info(f"---[处理文章][begin]: {article_url} ---")
    merchant_name = ""
    try:
        # 1. 获取 HTML
        response = retry_session.get(article_url, headers=REQUEST_HEADERS, timeout=30)
        response.raise_for_status()
        html_content = response.text

        # 2. 使用 BeautifulSoup 提取基础信息
        article_info = extract_content_bs(html_content, article_url)
        if not article_info:
            logger.error(f"无法从 {article_url} 提取文章内容。跳过。")
            return

        logger.info(f"文章标题: {article_info.articleTitle}")
        logger.info(f"发布时间: {article_info.articleDateTime}")
        images = article_info.articleImages
        logger.info(f"找到图片数量: {len(images)}")

        logger.info(f"开始提取机场信息")
        # 3. 使用 LLM 从文本提取机场/套餐信息
        llm_extracted_data = extract_info_llm(article_info.articleText)
        if llm_extracted_data:
            provider_name = article_info.articleTitle.split("---")[-1].strip() or llm_extracted_data.get(
                "provider_name")
            merchant_name = provider_name
            website_url = llm_extracted_data.get("provider_website")
            logger.info(f"机场信息提取结束  提取结果: Provider={provider_name}, Website={website_url}")
        else:
            logger.warning(f"未能从文章 {article_url} 的文本中通过 LLM 提取结构化信息。")
            return None

        # 如果无法确定机场名称，后续处理可能意义不大，可以选择跳过
        if not provider_name:
            logger.warning(f"无法确定文章 {article_url} 对应的机场名称，跳过 OCR 和存储。")
            return None

        # 4. 获取或创建机场商家记录
        merchant = sr_merchant_dao.find_or_create_merchant(
            name=provider_name,
            website_url=website_url,
            article_url=article_url,
            article_title=article_info.articleTitle
        )
        if not merchant or not merchant.id:
            logger.error(f"无法为机场 '{provider_name}' 创建或找到数据库记录。")
            return
        merchant_id = merchant.id
        logger.info(f"创建商家记录成功: {merchant.name} (ID: {merchant_id})")

        # 5. 处理图片：下载 -> OCR -> 存储记录
        for i, image_url in enumerate(images):
            # 提取节点信息并创建记录
            try:
                logger.info(f"[extract_and_save_record][begin]处理第 {i}/{len(images)} 张图片: {image_url}")
                extract_and_save_node_and_record(image_url, merchant_id, merchant_name, article_info)
                logger.info(f"[extract_and_save_record][end]第 {i}/{len(images)} 张图片提取保存完成")
                logger.info("=========================")
            except Exception as e:
                logger.exception(f"!!!![{merchant_name}]处理图片 {image_url} 时出错,已经跳过: {e}")
                continue
    except requests.exceptions.RequestException as e:
        logger.exception(f"[{merchant_name}]处理文章 {article_url} 时发生网络错误: {e}", exc_info=True)
    except Exception as e:
        logger.exception(f"[{merchant_name}]处理文章 {article_url} 时发生未知错误: {e}", exc_info=True)
    finally:
        logger.info(f"---[处理文章][end]: [{merchant_name}]完成 ---")
        logger.info("===========================================================================")


def main():
    """主执行函数"""
    logger.info("====== SR Scraper 启动 ======")
    start_time = datetime.now()

    # 1. 初始化数据库表
    logger.info("[prePost]初始化数据库...")
    create_tables()

    # 2. 获取需要爬取的文章 URL 列表
    # 可以从单个页面获取，也可以爬取多个分页，或从 RSS/Sitemap 获取
    logger.info("[prePost]获取文章 URL 列表...")
    article_urls_to_process = get_article_urls_from_all_page(ARTICLE_LIST_URL)

    if not article_urls_to_process:
        logger.warning("未能获取到任何文章 URL，程序退出。")
        return

    logger.info(f"准备处理 {len(article_urls_to_process)} 篇文章。")

    # 3. 遍历并处理每篇文章
    for i, url in enumerate(article_urls_to_process):
        logger.info(f"====商家处理进度: {i + 1}/{len(article_urls_to_process)}====")
        process_article(url)
    # 创建内存数据库并执行 SQL
    conn = sqlite3.connect(DATABASE_NAME)

    # 使用 Pandas 从内存数据库加载数据
    merchants_df = pd.read_sql_query("SELECT id, name FROM sr_merchant", conn)
    merchants_df.rename(columns={'id': 'merchant_id'}, inplace=True)

    speed_tests_df = pd.read_sql_query("SELECT * FROM sr_speed_test_record", conn)
    conn.close()  # 关闭数据库连接
    print("--- 原始测速记录 (部分) ---")
    print(speed_tests_df.head())
    evaluate_merchants(speed_tests_df, merchants_df, config.weights)
    end_time = datetime.now()
    logger.info(f"====== SR Scraper 运行结束 ======")
    logger.info(f"总耗时: {end_time - start_time}")


if __name__ == "__main__":
    main()

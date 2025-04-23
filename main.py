import json
# main.py
import logging
import time
from datetime import datetime
from typing import List
from urllib.parse import urljoin, urlparse

import requests  # 导入 requests 以便捕获其异常
from bs4 import BeautifulSoup  # 需要导入以获取列表页信息
from ocr_interface import process_image_ocr

from config import (
    TARGET_BLOG_BASE_URL, ARTICLE_LIST_URL, REQUEST_HEADERS, LOG_FILE  # 如果需要保存图片，则需要此配置
)
from content_extractor import extract_content_bs
from db import sr_merchant_dao, sr_node_dao, ssr_speed_test_record_dao
from db.db_connection import close_connection, create_connection
from db.db_connection import create_tables
from image_downloader import download_image, save_image  # 仅下载 bytes
from llm_interface import extract_info_llm
from models.SRNode import SRNode
from models.SSRSpeedTestRecord import SSRSpeedTestRecord
from scoring import calculate_all_scores
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
        logger.error(f"获取文章列表页面 {page_url} 失败: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"解析文章列表页面 {page_url} 时出错: {e}", exc_info=True)
        return []


def process_article(article_url: str):
    """处理单篇文章：提取、OCR、存储"""
    logger.info(f"--- 开始处理文章: {article_url} ---")
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
        logger.info(f"找到图片数量: {len(article_info.articleImages)}")

        # 3. 使用 LLM 从文本提取机场/套餐信息
        llm_extracted_data = extract_info_llm(article_info.articleText)
        provider_name = None
        website_url = None
        if llm_extracted_data:
            provider_name = llm_extracted_data.get("provider_name")
            website_url = llm_extracted_data.get("provider_website")
            # package_info = llm_extracted_data.get("package_info") # 可以存到 merchant 表或其他表
            # mentioned_nodes_text = llm_extracted_data.get("mentioned_nodes") # LLM 提取的节点信息
            logger.info(f"LLM 提取结果: Provider={provider_name}, Website={website_url}")
        else:
            logger.warning(f"未能从文章 {article_url} 的文本中通过 LLM 提取结构化信息。")
            # 备选策略：可以尝试从文章标题猜测机场名
            # provider_name = article_info.articleTitle.split('---')[-1].strip() # 非常不准确

        # 如果无法确定机场名称，后续处理可能意义不大，可以选择跳过
        if not provider_name:
            logger.warning(f"无法确定文章 {article_url} 对应的机场名称，跳过 OCR 和存储。")
            return

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
        logger.info(f"获取或创建商家记录: {merchant.name} (ID: {merchant_id})")

        # 5. 处理图片：下载 -> OCR -> 存储记录
        ocr_processed_count = 0
        for image_url in article_info.articleImages:
            image_bytes = download_image(image_url, retry_session)
            if not image_bytes:
                continue
            save_image(image_bytes, image_url)
            # 调用 OCR
            ocr_results, extracted_test_time = process_image_ocr(image_bytes)

            # 如果没有提取到表格记录，则跳过后续处理
            if not ocr_results:
                logger.warning(f"未能从图片 {image_url} (来源: {article_url}) 解析出 OCR 表格数据。")
                continue  # 跳到下一张图片

            # 确定有效的测试时间：优先使用图片中提取的，其次用文章发布时间
            effective_test_time = extracted_test_time or article_info.articleDateTime
            if extracted_test_time:
                logger.info(f"使用图片内提取的测试时间: {effective_test_time}")
            else:
                logger.info(f"图片内未找到测试时间，使用文章发布时间: {effective_test_time}")

            ocr_processed_count_for_image = 0  # 单张图片处理计数

            # 解析 OCR 结果并存入数据库
            for ocr_record in ocr_results:
                # -- 从 OCR 结果中提取关键字段 --
                # !! 列名需要与你的 OCR_EXPECTED_COLUMNS 和实际返回匹配 !!
                node_name_raw = ocr_record.get("节点名称")
                avg_speed_str = ocr_record.get("平均速度")
                max_speed_str = ocr_record.get("最高速度")
                tls_rtt_str = ocr_record.get("TLS RTT")
                https_delay_str = ocr_record.get("HTTPS 延迟")
                # 将其他所有列信息合并为一个 JSON 字符串，作为 unlock_info
                # 排除已单独提取的列和空值的列
                excluded_keys = {"节点名称", "平均速度", "最高速度", "TLS RTT", "HTTPS延迟", "序号", ""}  # 排除的列名
                other_info = {k: v for k, v in ocr_record.items() if k not in excluded_keys and v}
                unlock_info = json.dumps(other_info, ensure_ascii=False) if other_info else None

                if not node_name_raw:
                    logger.warning(f"OCR 记录缺少节点名称，跳过: {ocr_record}")
                    continue

                # 清理和转换数据
                node_name = node_name_raw.strip()

                # -- 需要健壮的数值转换，处理单位 (Mbps, Kbps, ms) --
                def parse_speed(speed_str):
                    if not speed_str: return None
                    try:
                        # 简单处理：去除单位，转换为 float (假设单位是 Mbps)
                        return float(str(speed_str).lower().replace('mbps', '').replace('kbps', '').replace(' ', ''))
                    except ValueError:
                        return None

                def parse_latency(latency_str):
                    if not latency_str: return None
                    try:
                        # 简单处理：去除 ms
                        return float(str(latency_str).lower().replace('ms', '').replace(' ', ''))
                    except ValueError:
                        return None

                avg_speed = parse_speed(avg_speed_str)
                max_speed = parse_speed(max_speed_str)
                tls_rtt = parse_latency(tls_rtt_str)
                https_delay = parse_latency(https_delay_str)

                # -- 处理测试时间 (已在上面确定 effective_test_time) --
                test_time = effective_test_time

            # -- 获取或创建节点记录 --
            # 简单的基于名称查找/创建。更复杂的可能需要结合 LLM 提取的区域信息
            node = sr_node_dao.find_or_create_node(node_name=node_name)  # 需要在 sr_node_dao 添加此函数
            if not node or not node.node_id:
                logger.error(f"无法为节点 '{node_name}' (来自机场 '{provider_name}') 创建或找到数据库记录。")
                continue
            node_id = node.node_id

            # -- 创建测速记录对象 --
            speed_test_record = SSRSpeedTestRecord(
                # UniqueID=None, # 由数据库生成
                airport_id=merchant_id,
                airport_name=provider_name,
                node_id=node_id,
                node_name=node_name,
                average_speed=avg_speed,
                max_speed=max_speed,
                tls_rtt=tls_rtt,
                https_delay=https_delay,
                unlock_info=unlock_info,
                test_time=test_time,  # 使用文章发布时间或 OCR 时间
                # insert_time=None, # 由数据库 DEFAULT
                # update_time=None, # 由数据库更新
                host_info=None  # 可以记录测试环境信息
            )

            # -- 插入数据库 --
            created = ssr_speed_test_record_dao.create_record(speed_test_record)
            if created:
                ocr_processed_count_for_image += 1
                ocr_processed_count += 1  # 更新总计数

        if ocr_processed_count > 0:
            logger.info(f"成功处理图片 {image_url} 并存储了 {ocr_processed_count} 条 OCR 记录。")

    except requests.exceptions.RequestException as e:
        logger.error(f"处理文章 {article_url} 时发生网络错误: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"处理文章 {article_url} 时发生未知错误: {e}", exc_info=True)
    finally:
        logger.info(f"--- 完成处理文章: {article_url} ---")


def main():
    """主执行函数"""
    logger.info("====== SR Scraper 启动 ======")
    start_time = datetime.now()

    # 1. 初始化数据库表
    logger.info("初始化数据库...")
    create_tables()

    # 2. 获取需要爬取的文章 URL 列表
    # 可以从单个页面获取，也可以爬取多个分页，或从 RSS/Sitemap 获取
    logger.info("获取文章 URL 列表...")
    article_urls_to_process = get_article_urls_from_all_page(ARTICLE_LIST_URL)

    if not article_urls_to_process:
        logger.warning("未能获取到任何文章 URL，程序退出。")
        return

    logger.info(f"准备处理 {len(article_urls_to_process)} 篇文章。")

    # 3. 遍历并处理每篇文章
    for i, url in enumerate(article_urls_to_process):
        logger.info(f"处理进度: {i + 1}/{len(article_urls_to_process)}")
        process_article(url)
        # 可以加个延时避免请求过于频繁
        time.sleep(1)

    # 4. (可选) 处理完成后计算得分
    logger.info("所有文章处理完毕，开始计算得分...")
    final_scores = calculate_all_scores()
    print("\n" + "=" * 20 + " 最终得分排名 " + "=" * 20)
    if final_scores:
        # 格式化输出得分
        for merchant, nodes in final_scores.items():
            avg_m_score = sum(nodes.values()) / len(nodes) if nodes else 0
            print(f"\n{merchant} (平均分: {avg_m_score:.2f})")
            # 只显示前 N 个节点或全部显示
            node_count = 0
            for node, score in nodes.items():
                print(f"  - {node}: {score:.2f}")
                node_count += 1
                # if node_count >= 10: # 示例：最多显示10个
                #     print("  ...")
                #     break
    else:
        print("未能计算任何得分。")
    print("=" * 50)

    end_time = datetime.now()
    logger.info(f"====== SR Scraper 运行结束 ======")
    logger.info(f"总耗时: {end_time - start_time}")


if __name__ == "__main__":
    # --- 添加 sr_node_dao.find_or_create_node 的实现 ---
    # 这个函数很重要，需要在 db/sr_node_dao.py 中添加
    def find_or_create_node(node_name: str, node_type: str | None = None, region: str | None = None) -> SRNode | None:
        conn = create_connection()
        cursor = conn.cursor()
        try:
            # 尝试查找
            cursor.execute("SELECT * FROM sr_node WHERE node_name = ?", (node_name,))
            row = cursor.fetchone()
            if row:
                logger.debug(f"找到已存在的节点: {node_name} (ID: {row['id']})")
                # 将 sqlite3.Row 转换为 SRNode 对象
                # 注意：数据库列名为 id，模型字段名为 node_id
                return SRNode(node_id=row['id'], node_name=row['node_name'], type=row['type'], region=row['region'])
            else:
                # 创建
                logger.info(f"未找到节点 '{node_name}', 准备创建新记录...")
                cursor.execute('''
                    INSERT INTO sr_node (node_name, type, region, gmt_modified)
                    VALUES (?, ?, ?, ?)
                 ''', (node_name, node_type, region, datetime.now()))
                conn.commit()
                new_id = cursor.lastrowid
                logger.info(f"成功创建节点: {node_name} (ID: {new_id})")
                return SRNode(node_id=new_id, node_name=node_name, type=node_type, region=region)
        finally:
            close_connection(conn)


    # 将函数添加到 sr_node_dao 模块 (运行时动态添加，或者直接修改文件)
    sr_node_dao.find_or_create_node = find_or_create_node
    # ----------------------------------------------------

    main()

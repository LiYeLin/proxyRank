import logging

from db.db_connection import create_tables
from db.sr_merchant_dao import create_merchant, get_merchant_by_article_url
from models.SRMerchant import SRMerchant
from spider.spider import get_article_url_list, get_speed_test_info
from utils.logger_config import setup_logging

logger = setup_logging(log_level=logging.INFO, log_file='app_default.log')


def main():

    blog_url = "https://www.duyaoss.com/"  # 替换为目标博客 URL
    # 获取文章列表
    articles = get_article_url_list(blog_url)
    speedTestArticles = [item for item in articles if "测速" in item.articleTitle]

    # 获取每个文章中的测试信息图片
    for item in speedTestArticles:
        item.articleImages = get_speed_test_info(item.articleUrl)
    # 转dict 打印
    articles_data = [article.to_dict() for article in speedTestArticles]
    logger.info("采集到文章共{}条：{}".format(len(articles_data), articles_data))

    create_tables()
    for article in speedTestArticles:
        record = get_merchant_by_article_url(article.articleUrl)
        if record:
            logger.info(f"已经保存 跳过{article.articleTitle}")
            continue
        mer = SRMerchant()
        mer.article_title = article.articleTitle
        mer.article_url = article.articleUrl
        mer.name
        create_merchant(mer)
        logger.info(f"插入商家数据成功{article.articleTitle}")



# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    logger = setup_logging(log_level=logging.INFO, log_file='app_default.log')
    main()

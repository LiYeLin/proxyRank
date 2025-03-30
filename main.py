import logging

from spider.spider import get_article_url_list, get_speed_test_info
from utils.logger_config import setup_logging

logger = setup_logging(log_level=logging.INFO, log_file='app_default.log')


def main():
    blog_url = "https://www.duyaoss.com/"  # 替换为目标博客 URL
    articles = get_article_url_list(blog_url)
    speedTestArticles = [item for item in articles if "测速" in item.articleTitle]
    for item in speedTestArticles:
        item.articleImages = get_speed_test_info(item.articleUrl)
    articles_data = [article.to_dict() for article in speedTestArticles]
    logger.info("采集到文章共{}条：{}".format(len(articles_data), articles_data))



# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    logger = setup_logging(log_level=logging.INFO, log_file='app_default.log')
    main()

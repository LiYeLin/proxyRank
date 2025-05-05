# config.py
import os

from dotenv import load_dotenv

# 加载 .env 文件中的环境变量 (如果使用 .env)
load_dotenv()

# --- 数据库配置 ---
DATABASE_NAME = 'speed_test.db'

# --- 目标网站配置 ---
# !! 修改为你需要爬取的博客基础 URL
TARGET_BLOG_BASE_URL = "https://www.duyaoss.com"
# !! 修改为获取文章列表的 URL 或方式 (例如 RSS feed, sitemap, 或特定分类页面)
# 这个需要根据具体网站结构确定
ARTICLE_LIST_URL = f"{TARGET_BLOG_BASE_URL}/category/%E6%9C%BA%E5%9C%BA%E6%B5%8B%E9%80%9F/" # 示例：测速分类页

# --- API 密钥配置 ---
# 建议使用环境变量存储敏感信息
# !! 填入你的阿里云 OCR AccessKey 和 Secret
ALIYUN_OCR_ACCESS_KEY_ID = os.getenv("ALIYUN_OCR_ACCESS_KEY_ID", "YOUR_ACCESS_KEY_ID")
ALIYUN_OCR_ACCESS_KEY_SECRET = os.getenv("ALIYUN_OCR_ACCESS_KEY_SECRET", "YOUR_ACCESS_KEY_SECRET")
# !! 填入你的阿里云 OCR Endpoint (根据地域选择)
ALIYUN_OCR_ENDPOINT = os.getenv("ALIYUN_OCR_ENDPOINT", "ocr-api.cn-hangzhou.aliyuncs.com") # 示例：杭州

# !! 填入你的阿里云百炼/DashScope API Key !!
# 通常可以在 DashScope 控制台获取 (https://dashscope.console.aliyun.com/apiKey)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "YOUR_DASHSCOPE_API_KEY")
# !! 填入你计划在百炼上使用的具体模型 ID !!
# 例如: qwen-turbo, qwen-plus, qwen-max, 或百炼平台上的自定义模型ID
BAILIAN_MODEL_ID = os.getenv("BAILIAN_MODEL_ID", "qwen-plus") # 示例模型，请替换为你需要使用的

# !! Model for IMAGE extraction (Multimodal Model) !!
# Common choices: qwen-vl-plus, qwen-vl-max
BAILIAN_VL_MODEL_ID = os.getenv("BAILIAN_VL_MODEL_ID", "qwen-vl-plus") # Use a VL model

# --- 其他配置 ---
# 图片下载目录
IMAGE_DOWNLOAD_DIR = "downloaded_images"
# 日志文件
LOG_FILE = 'app_default.log'
# 请求头
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- LLM 相关配置 ---
LLM_EXTRACTION_PROMPT = """
从以下的博客文章内容中提取网络代理服务商（机场）的相关信息。请以 JSON 格式返回结果，包含以下字段：
- "provider_name": 字符串，机场的名称(如：小旋风/奶昔/奶油/nano等）。如果文章主体不是评测单一机场，则留空。
- "provider_website": 字符串，机场的官方网址（如果有提及）。
- "package_info": 列表，每个元素是一个包含 "name" (套餐名称) 和 "price" (价格描述) 的字典。
- "mentioned_nodes": 列表，文章中明确提到的节点名称或区域。

如果某项信息未在文本中明确提及，请将对应字段的值设为 null 或空列表。

文章内容：
{article_text}

JSON 结果：
"""


# !! Prompt for IMAGE extraction (OCR replacement) !!
LLM_IMAGE_EXTRACTION_PROMPT = """
请结构化这个图片中的信息，并且以json对象的格式输出，对象包含两个字段：test_time （测试时间，从图片中的表格的最后一行提取）/test_record_list 从图片中的表格的其他行提取
最后一行会有形如：‘测试时间：2024-10-09 21：07：14（CST），本测试为试验性结果，仅供参考。’的字样，请提取其中时间 并且以yyyy-mm-dd hh:mm:ss的形式放在输出对象test_time字段中
test_record_list列表中的每个对象代表表格中的一行数据，每个对象我只在乎:[序号, 节点名称, 类型, 平均速度, 最高速度, TLS RTT, HTTPS延迟]这几个字段。
如果某行缺少某个字段的值，请将该字段的值设为 null 或空字符串。
！！！请注意 尽可能的提取每一行信息
你输出的内容应该形如：
{
  "test_time":"2024-10-09 21:07:14",
  "test_record_list":[
    {
        "序号": 1,
        "节点名称": "官网：stc.zone",
        "类型": "ShadowsocksR",
        "平均速度": "0",
        "最高速度": "0",
        "TLSRTT": "-",
        "HTTPS延迟": "-"
    },
    {
        "序号": 2,
        "节点名称": "引导页：bit.ly/3sWoAZU",
        "类型": "ShadowsocksR",
        "平均速度": "0",
        "最高速度": "0",
        "TLSRTT": "-",
        "HTTPS延迟": "-"
    },
    {
        "序号": 3,
        "节点名称": "香港 05 (0.5x)",
        "类型": "ShadowsocksR",
        "平均速度": "46.1",
        "最高速度": "67.3",
        "TLSRTT": "137",
        "HTTPS延迟": "120"
    },
    ......
]
}
"""

# --- OCR 相关配置 ---
# 根据你的 OCR 模型和需求调整
REQUIRED_KEYS = ["节点名称", "平均速度", "最高速度", "TLSRTT", "HTTPS延迟"] # 示例列名

# 定义权重
weights = {
    'avg_speed': 0.3,
    'max_speed': 0.1,
    'tls_rtt': 0.2,
    'https_latency': 0.4
}
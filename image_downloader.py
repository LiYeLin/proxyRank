# image_downloader.py
import hashlib
import logging
import os
from urllib.parse import urlparse

from google.auth.transport import requests

from config import IMAGE_DOWNLOAD_DIR, REQUEST_HEADERS
from utils.RetrySession import RetrySession

logger = logging.getLogger(__name__)


def download_image(image_url: str, session: RetrySession) -> bytes | None:
    """下载图片并返回其二进制内容"""
    try:
        logger.info(f"尝试下载图片: {image_url}")
        response = session.get(image_url, headers=REQUEST_HEADERS, stream=True, timeout=30)  # 设置超时
        response.raise_for_status()  # 检查 HTTP 错误状态

        # 检查 Content-Type 是否真的是图片
        content_type = response.headers.get('content-type', '').lower()
        if not content_type.startswith('image/'):
            logger.warning(f"链接 {image_url} 的 Content-Type 不是图片 ({content_type})，跳过下载。")
            return None

        image_bytes = response.content  # 读取内容
        logger.info(f"成功下载图片: {image_url} ({len(image_bytes)} bytes)")
        return image_bytes

    except requests.exceptions.RequestException as e:
        logger.error(f"下载图片 {image_url} 时发生网络错误: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"下载图片 {image_url} 时发生未知错误: {e}", exc_info=True)
        return None


def save_image(image_bytes: bytes, original_url: str) -> str | None:
    """将图片字节保存到本地文件，并返回文件路径"""
    if not os.path.exists(IMAGE_DOWNLOAD_DIR):
        try:
            os.makedirs(IMAGE_DOWNLOAD_DIR)
            logger.info(f"创建图片下载目录: {IMAGE_DOWNLOAD_DIR}")
        except OSError as e:
            logger.error(f"无法创建图片下载目录 {IMAGE_DOWNLOAD_DIR}: {e}", exc_info=True)
            return None

    try:
        # 使用 URL 的 hash 或内容 hash 作为文件名避免重复和特殊字符问题
        hasher = hashlib.sha1()
        hasher.update(image_bytes)
        image_hash = hasher.hexdigest()

        # 尝试从 URL 获取文件扩展名
        parsed_url = urlparse(original_url)
        filename, ext = os.path.splitext(os.path.basename(parsed_url.path))
        if not ext or len(ext) > 5:  # 简单的扩展名检查
            # 可以根据 image_bytes 的 magic number 判断更准确的类型，但这里简化处理
            ext = '.png'  # 默认 .png，或者根据 content-type 判断

        save_path = os.path.join(IMAGE_DOWNLOAD_DIR, f"{image_hash}{ext}")
        # 判断图片是否已经存在
        if os.path.exists(save_path):
            logger.info(f"图片已存在: {save_path}")
            return save_path
        with open(save_path, 'wb') as f:
            f.write(image_bytes)
        logger.info(f"图片已保存到: {save_path}")
        return save_path

    except Exception as e:
        logger.error(f"保存图片 (来源: {original_url}) 时出错: {e}", exc_info=True)
        return None

# logger_config.py
import logging
def setup_logging(log_level=logging.INFO, log_file='app_default.log'):
    logger = logging.getLogger()  # 获取 root logger
    logger.setLevel(logging.DEBUG)

    # 移除之前可能存在的 handlers，避免重复写入
    if logger.hasHandlers():
        logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger  # 返回配置好的 root logger


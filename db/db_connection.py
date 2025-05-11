# db_connection.py
import logging
import sqlite3

from config import LOG_FILE
from utils.logger_config import setup_logging

DATABASE_NAME = 'speed_test.db'
logger = setup_logging(log_level=logging.INFO, log_file=LOG_FILE)


def create_connection():
    """创建数据库连接"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # 将查询结果作为字典返回
    return conn


def close_connection(conn):
    """关闭数据库连接"""
    if conn:
        conn.close()


def create_tables():
    """创建数据库表（如果不存在）"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sr_merchant (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gmt_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                gmt_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                name TEXT,
                website_url TEXT,
                article_url TEXT,
                article_title TEXT,
                UNIQUE(name)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sr_node (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                gmt_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                gmt_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                merchant_id INTEGER,
                merchant_name TEXT,
                node_name TEXT,
                type TEXT,
                FOREIGN KEY (merchant_id) REFERENCES sr_merchant(id),
                UNIQUE(merchant_id,node_name)
            )
        ''')
        cursor.execute('''
                        CREATE TABLE IF NOT EXISTS sr_merchant_speed_test_pic (
                                "id"	INTEGER,
                                "merchant_id"	INTEGER,
                                "pic_md5"	TEXT UNIQUE,
                                "pic_url"	TEXT,
                                "pic_path"	TEXT,
                                "test_time"	TEXT,
                                "model_return"	TEXT,
                                PRIMARY KEY("id"),
                                FOREIGN KEY("merchant_id") REFERENCES "sr_merchant"("id")
            )
                ''')
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sr_speed_test_record (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        gmt_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        gmt_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        pic_id INTEGER,
                        merchant_id INTEGER NOT NULL,
                        merchant_name TEXT NOT NULL,
                        node_id INTEGER NOT NULL,
                        node_name TEXT NOT NULL,
                        average_speed REAL NOT NULL,
                        max_speed REAL NOT NULL,
                        tls_rtt REAL,
                        https_delay REAL,
                        test_time DATETIME,
                        host_info TEXT,
                        	UNIQUE("merchant_id","node_id","pic_id","test_time")

                    )
                ''')


        conn.commit()
        logger.info("数据库表创建成功或已存在。")
    except sqlite3.Error as e:
        logger.exception(f"创建表时发生错误: {e}")
    finally:
        close_connection(conn)

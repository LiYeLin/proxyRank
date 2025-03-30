# db_connection.py
import sqlite3

DATABASE_NAME = 'speed_test.db'

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
            CREATE TABLE IF NOT EXISTS sr_speed_test_record (
                UniqueID INTEGER PRIMARY KEY AUTOINCREMENT,
                airport_id INTEGER,
                airport_name TEXT,
                node_id INTEGER,
                node_name TEXT,
                average_speed REAL,
                max_speed REAL,
                tls_rtt REAL,
                https_delay REAL,
                unlock_info TEXT,
                test_time DATETIME,
                insert_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME,
                host_info TEXT,
                FOREIGN KEY (airport_id) REFERENCES sr_merchant(id),
                FOREIGN KEY (node_id) REFERENCES sr_node(node_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sr_merchant (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                website_url TEXT,
                article_url TEXT,
                article_title TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sr_node (
                node_id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_name TEXT,
                type TEXT,
                region TEXT
            )
        ''')
        conn.commit()
        print("数据库表创建成功或已存在。")
    except sqlite3.Error as e:
        print(f"创建表时发生错误: {e}")
    finally:
        close_connection(conn)





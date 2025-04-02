import sqlite3

from db.db_connection import close_connection, create_connection
from models.SRMerchant import SRMerchant


# 机场信息表 CRUD
def create_merchant(merchant: SRMerchant):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO sr_merchant (name, website_url, article_url, article_title)
            VALUES (?, ?, ?, ?)
        ''', (merchant.name, merchant.website_url, merchant.article_url, merchant.article_title))
        conn.commit()
        merchant.id = cursor.lastrowid
        return merchant
    except sqlite3.Error as e:
        print(f"创建机场信息失败: {e}")
        return None
    finally:
        close_connection(conn)

def get_merchant_by_article_url(article_url):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sr_merchant WHERE article_url = ?", (article_url,))
        row = cursor.fetchone()
        if row:
            return SRMerchant(**row)
        return None
    except sqlite3.Error as e:
        print(f"获取机场信息失败: {e}")
        return None
    finally:
        close_connection(conn)

def update_merchant(merchant: SRMerchant):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE sr_merchant
            SET name = ?, website_url = ?, article_url = ?, article_title = ?
            WHERE id = ?
        ''', (merchant.name, merchant.website_url, merchant.article_url, merchant.article_title, merchant.id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"更新机场信息失败: {e}")
        return False
    finally:
        close_connection(conn)

def delete_merchant(merchant_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sr_merchant WHERE id = ?", (merchant_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"删除机场信息失败: {e}")
        return False
    finally:
        close_connection(conn)
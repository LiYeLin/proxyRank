# db/sr_merchant_dao.py
import logging
import sqlite3
from datetime import datetime

from db.db_connection import create_connection, close_connection
from models.SRMerchant import SRMerchant

logger = logging.getLogger(__name__)

def create_merchant(merchant: SRMerchant) -> SRMerchant | None:
    """创建新的机场商家信息"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO sr_merchant (name, website_url, article_url, article_title, gmt_modified)
            VALUES (?, ?, ?, ?, ?)
        ''', (merchant.name, merchant.website_url, merchant.article_url, merchant.article_title, datetime.now()))
        conn.commit()
        merchant.id = cursor.lastrowid
        logger.info(f"成功创建商家: {merchant.name} (ID: {merchant.id})")
        return merchant
    except sqlite3.Error as e:
        logger.error(f"创建商家信息 '{merchant.name}' 失败: {e}", exc_info=True)
        return None
    finally:
        close_connection(conn)

def get_merchant_by_id(merchant_id: int) -> SRMerchant | None:
    """根据 ID 获取商家信息"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sr_merchant WHERE id = ?", (merchant_id,))
        row = cursor.fetchone()
        if row:
            # sqlite3.Row 可以像字典一样访问列名
            return SRMerchant(
                id=row['id'],
                name=row['name'],
                website_url=row['website_url'],
                article_url=row['article_url'],
                article_title=row['article_title']
                # gmt_create, gmt_modified 可以选择性加载
            )
        return None
    except sqlite3.Error as e:
        logger.error(f"获取商家信息 (ID: {merchant_id}) 失败: {e}", exc_info=True)
        return None
    finally:
        close_connection(conn)

def get_merchant_by_name(name: str) -> SRMerchant | None:
    """根据名称获取商家信息 (假设名称基本唯一)"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sr_merchant WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
             return SRMerchant(
                id=row['id'],
                name=row['name'],
                website_url=row['website_url'],
                article_url=row['article_url'],
                article_title=row['article_title']
            )
        return None
    except sqlite3.Error as e:
        logger.error(f"根据名称 '{name}' 获取商家信息失败: {e}", exc_info=True)
        return None
    finally:
        close_connection(conn)


def find_or_create_merchant(name: str, website_url: str | None = None, article_url: str | None = None, article_title: str | None = None) -> SRMerchant | None:
    """尝试通过名称查找商家，如果不存在则创建"""
    existing_merchant = get_merchant_by_name(name)
    if existing_merchant:
        # 可以选择更新信息 (例如最新的 article_url)
        # update_merchant(...)
        logger.debug(f"找到已存在的商家: {name} (ID: {existing_merchant.id})")
        return existing_merchant
    else:
        logger.info(f"未找到商家 '{name}', 准备创建新记录...")
        new_merchant = SRMerchant(
            name=name,
            website_url=website_url,
            article_url=article_url,
            article_title=article_title
        )
        return create_merchant(new_merchant)


def update_merchant(merchant: SRMerchant) -> bool:
    """更新商家信息"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE sr_merchant
            SET name = ?, website_url = ?, article_url = ?, article_title = ?, gmt_modified = ?
            WHERE id = ?
        ''', (merchant.name, merchant.website_url, merchant.article_url, merchant.article_title, datetime.now(), merchant.id))
        conn.commit()
        logger.info(f"成功更新商家: {merchant.name} (ID: {merchant.id})")
        return True
    except sqlite3.Error as e:
        logger.error(f"更新商家信息 '{merchant.name}' (ID: {merchant.id}) 失败: {e}", exc_info=True)
        return False
    finally:
        close_connection(conn)

def delete_merchant(merchant_id: int) -> bool:
    """删除商家信息"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        # 注意：删除商家前可能需要处理关联的测速记录 (设置外键 ON DELETE CASCADE 或手动删除)
        cursor.execute("DELETE FROM sr_merchant WHERE id = ?", (merchant_id,))
        conn.commit()
        logger.info(f"成功删除商家 (ID: {merchant_id})")
        return True
    except sqlite3.Error as e:
        logger.error(f"删除商家 (ID: {merchant_id}) 失败: {e}", exc_info=True)
        return False
    finally:
        close_connection(conn)
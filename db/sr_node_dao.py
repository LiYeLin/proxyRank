import logging
import sqlite3
from datetime import datetime

from config import LOG_FILE
from db.db_connection import create_connection, close_connection
from models.SRNode import SRNode
from utils.logger_config import setup_logging

logger = setup_logging(log_level=logging.INFO, log_file=LOG_FILE)


def find_or_create_node(sr_node: SRNode) -> SRNode | None:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        # 尝试查找
        cursor.execute("SELECT * FROM sr_node WHERE node_name = ? and merchant_id = ?",
                       (sr_node.node_name, sr_node.merchant_id))
        row = cursor.fetchone()
        if row:
            logger.debug(f"找到已存在的节点: {sr_node.node_name} (ID: {row['id']})")
            # 将 sqlite3.Row 转换为 SRNode 对象
            # 注意：数据库列名为 id，模型字段名为 node_id
            return SRNode(row['id'], row['node_name'], row['type'], row['merchant_id'], row['merchant_name'])
        else:
            # 创建
            logger.info(f"未找到节点 '{sr_node.node_name}', 准备创建新记录...")
            cursor.execute('''
                INSERT INTO sr_node (node_name, type, merchant_id,merchant_name, gmt_modified)
                VALUES (?, ?, ?, ?, ?)
             ''', (sr_node.node_name, sr_node.type, sr_node.merchant_id, sr_node.merchant_name, datetime.now()))
            conn.commit()
            sr_node.node_id = cursor.lastrowid
            logger.info(f"成功创建节点: {sr_node.node_name} (ID: {sr_node.node_id})")
            return sr_node
    finally:
        close_connection(conn)


# 节点信息表 CRUD
def create_node(node: SRNode):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO sr_node (node_name, type, region)
            VALUES (?, ?, ?)
        ''', (node.node_name, node.type, node.region))
        conn.commit()
        node.node_id = cursor.lastrowid
        return node
    except sqlite3.Error as e:
        print(f"创建节点信息失败: {e}")
        return None
    finally:
        close_connection(conn)


def get_node_by_id(node_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sr_node WHERE node_id = ?", (node_id,))
        row = cursor.fetchone()
        if row:
            return SRNode(**row)
        return None
    except sqlite3.Error as e:
        print(f"获取节点信息失败: {e}")
        return None
    finally:
        close_connection(conn)


def update_node(node: SRNode):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE sr_node
            SET node_name = ?, type = ?, region = ?
            WHERE node_id = ?
        ''', (node.node_name, node.type, node.region, node.node_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"更新节点信息失败: {e}")
        return False
    finally:
        close_connection(conn)


def delete_node(node_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sr_node WHERE node_id = ?", (node_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"删除节点信息失败: {e}")
        return False
    finally:
        close_connection(conn)

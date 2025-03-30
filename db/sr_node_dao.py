import sqlite3

from db.db_connection import create_connection, close_connection
from models.SRNode import SRNode


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
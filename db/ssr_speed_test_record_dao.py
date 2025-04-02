import sqlite3
from datetime import datetime

from db.db_connection import create_connection, close_connection
from models.SSRSpeedTestRecord import SSRSpeedTestRecord


# 测速记录表 CRUD
def create_speed_record(record: SSRSpeedTestRecord):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO sr_speed_test_record (gmt_create,gmt_modified,airport_id, airport_name, node_id, node_name,
                                                average_speed, max_speed, tls_rtt, https_delay,
                                                unlock_info, test_time, update_time, host_info)
            VALUES (now(),now(),?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (record.airport_id, record.airport_name, record.node_id, record.node_name,
              record.average_speed, record.max_speed, record.tls_rtt, record.https_delay,
              record.unlock_info, record.test_time, datetime.now(), record.host_info))
        conn.commit()
        record.UniqueID = cursor.lastrowid
        return record
    except sqlite3.Error as e:
        print(f"创建测速记录失败: {e}")
        return None
    finally:
        close_connection(conn)

def get_speed_record_by_id(record_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sr_speed_test_record WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if row:
            return SSRSpeedTestRecord(**row)
        return None
    except sqlite3.Error as e:
        print(f"获取测速记录失败: {e}")
        return None
    finally:
        close_connection(conn)

def get_all_speed_records():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sr_speed_test_record")
        rows = cursor.fetchall()
        return [SSRSpeedTestRecord(**row) for row in rows]
    except sqlite3.Error as e:
        print(f"获取所有测速记录失败: {e}")
        return None
    finally:
        close_connection(conn)

def update_speed_record(record: SSRSpeedTestRecord):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE sr_speed_test_record
            SET airport_id = ?, airport_name = ?, node_id = ?, node_name = ?,
                average_speed = ?, max_speed = ?, tls_rtt = ?, https_delay = ?,
                unlock_info = ?, test_time = ?, update_time = ?, host_info = ? ,gmt_modified = now()
            WHERE id = ?
        ''', (record.airport_id, record.airport_name, record.node_id, record.node_name,
              record.average_speed, record.max_speed, record.tls_rtt, record.https_delay,
              record.unlock_info, record.test_time, datetime.now(), record.host_info, record.UniqueID))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"更新测速记录失败: {e}")
        return False
    finally:
        close_connection(conn)

def delete_speed_record(record_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sr_speed_test_record WHERE id = ?", (record_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"删除测速记录失败: {e}")
        return False
    finally:
        close_connection(conn)
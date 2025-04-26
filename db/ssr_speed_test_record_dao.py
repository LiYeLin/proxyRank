# db/ssr_speed_test_record_dao.py
import logging
import sqlite3
from datetime import datetime
from typing import List

from db.db_connection import create_connection, close_connection
from models.SSRSpeedTestRecord import SSRSpeedTestRecord  # 假设你把 UniqueID 改成了 id

logger = logging.getLogger(__name__)

# 注意：SSRSpeedTestRecord 模型中的字段名与数据库表列名不完全一致
# 例如 UniqueID vs id, airport_id vs merchant_id, airport_name vs merchant_name
# DAO 函数在插入和查询时需要做映射

def create_record(record: SSRSpeedTestRecord) -> SSRSpeedTestRecord | None:
    """创建新的测速记录"""
    conn = create_connection()
    cursor = conn.cursor()
    # 将模型字段映射到数据库列名
    sql = '''
        INSERT INTO sr_speed_test_record (
            merchant_id, merchant_name, node_id, node_name, average_speed,
            max_speed, tls_rtt, https_delay, test_time,
            host_info, gmt_modified,pic_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
    '''
    params = (
        record.airport_id, record.airport_name, record.node_id, record.node_name, record.average_speed,
        record.max_speed, record.tls_rtt, record.https_delay,  record.test_time,
        record.host_info, datetime.now(),record.pic_id
    )
    try:
        cursor.execute(sql, params)
        conn.commit()
        record_id = cursor.lastrowid # 获取自增主键
        # !! 注意：SSRSpeedTestRecord 模型没有 id 字段，但数据库有。
        # 你可以考虑给模型加上 id，或者在 DAO 返回时不填充 id。
        # 这里假设模型需要 id
        # record.UniqueID = record_id # 如果 UniqueID 就是数据库的 id
        logger.info(f"成功创建测速记录 (ID: {record_id}) for {record.airport_name} - {record.node_name}")
        # 如果模型有 id 字段:
        # record.id = record_id
        return record # 或者根据 ID 重新查询一次以获取完整信息包括 gmt_create
    except sqlite3.Error as e:
        logger.exception(f"创建测速记录 for {record.airport_name} - {record.node_name} 失败: {e}", exc_info=True)
        return None
    finally:
        close_connection(conn)

def get_records_by_merchant(merchant_id: int) -> List[SSRSpeedTestRecord]:
    """获取指定商家的所有测速记录"""
    conn = create_connection()
    cursor = conn.cursor()
    records = []
    try:
        cursor.execute("SELECT * FROM sr_speed_test_record WHERE merchant_id = ? ORDER BY test_time DESC", (merchant_id,))
        rows = cursor.fetchall()
        for row in rows:
            # 将数据库列映射回模型字段
            records.append(
                SSRSpeedTestRecord(UniqueID=row['id'], airport_id=row['merchant_id'], airport_name=row['merchant_name'],
                                   node_id=row['node_id'], node_name=row['node_name'],
                                   average_speed=row['average_speed'], max_speed=row['max_speed'],
                                   tls_rtt=row['tls_rtt'], https_delay=row['https_delay'], test_time=row['test_time'],
                                   host_info=row['host_info']))
        return records
    except sqlite3.Error as e:
        logger.exception(f"获取商家 (ID: {merchant_id}) 的测速记录失败: {e}", exc_info=True)
        return []
    finally:
        close_connection(conn)

# --- 可以根据需要添加更多查询函数 ---
# 例如：get_records_by_node, get_records_in_daterange 等
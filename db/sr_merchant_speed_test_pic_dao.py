# db/ssr_speed_test_record_dao.py
import logging
import sqlite3

from db.db_connection import create_connection, close_connection
from models.SRMerchantSpeedTestPic import SRMerchantSpeedTestPic

logger = logging.getLogger(__name__)


def create_pic_record(record: SRMerchantSpeedTestPic) -> SRMerchantSpeedTestPic | None:
    """创建新的测速记录"""
    conn = create_connection()
    cursor = conn.cursor()
    # 将模型字段映射到数据库列名
    sql = '''
        INSERT INTO sr_merchant_speed_test_pic (
merchant_id,
pic_md5,
pic_url,
pic_path,
test_time,
model_return
        ) VALUES (?, ?, ?, ?, ?, ?)
    '''
    params = (
        record.merchant_id, record.pic_md5, record.pic_url, record.pic_path, record.test_time,
        record.model_return
    )
    try:
        cursor.execute(sql, params)
        conn.commit()
        record_id = cursor.lastrowid  # 获取自增主键
        logger.info(f"成功创建图片记录 (ID: {record_id}) for {record.pic_url} - {record.pic_url}")
        # 如果模型有 id 字段:
        record.id = record_id
        return record  # 或者根据 ID 重新查询一次以获取完整信息包括 gmt_create
    except sqlite3.Error as e:
        logger.exception(f"创建创建图片记录 for {record.merchant_id} 失败: {e}", exc_info=True)
        return None
    finally:
        close_connection(conn)


def query_pic_record_by_md5(md5: str) -> SRMerchantSpeedTestPic | None:
    """根据 md5 查询记录"""
    conn = create_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM sr_merchant_speed_test_pic WHERE pic_md5 = ?"
    cursor.execute(sql, (md5,))
    row = cursor.fetchone()
    # 将 sqlite3.Row 转换为 SRMerchantSpeedTestPic 对象
    if not row:
        return None
    return SRMerchantSpeedTestPic(id = row['id'],merchant_id=row['merchant_id'], pic_md5=row['pic_md5'], pic_url=row['pic_url'],
                                  pic_path=row['pic_path'], test_time=row['test_time'],
                                  model_return=row['model_return'])

# scoring.py
import logging
from datetime import datetime
from typing import List, Dict

from models.SSRSpeedTestRecord import SSRSpeedTestRecord

logger = logging.getLogger(__name__)

def calculate_node_score(records: List[SSRSpeedTestRecord]) -> float:
    """
    计算单个节点的得分。
    这是一个非常基础的示例，你需要根据你的需求设计复杂的加权算法。
    """
    if not records:
        return 0.0

    # 示例：简单地对最近 N 天的平均速度求平均值，并考虑 RTT
    # 权重可以根据时间衰减
    score = 0.0
    total_weight = 0.0
    now = datetime.now()

    # 过滤掉无效数据 (例如速度或 RTT 为 0 或 None)
    valid_records = [
        r for r in records
        if r.average_speed is not None and r.average_speed > 0 and \
           r.tls_rtt is not None and r.tls_rtt > 0 and \
           r.test_time is not None # 确保有测试时间
    ]
    if not valid_records:
         return 0.0

    # 按测试时间排序，最新的在前
    valid_records.sort(key=lambda r: r.test_time, reverse=True)

    for record in valid_records:
         # --- 时间衰减权重 ---
         time_diff = now - record.test_time
         days_ago = time_diff.total_seconds() / (60 * 60 * 24)

         # 示例权重：7天内权重为1，超过30天权重很低
         weight = 0.0
         if days_ago <= 7:
             weight = 1.0
         elif days_ago <= 30:
             weight = max(0, 1 - (days_ago - 7) / 23) # 线性衰减
         else:
             weight = 0.1 # 给旧数据一个很小的基础权重

         # --- 指标得分计算 ---
         # 速度：越高越好 (可以进行归一化)
         speed_score = record.average_speed # 简单使用原始值

         # 延迟：越低越好 (可以进行反转和归一化)
         # 假设 RTT 低于 50ms 满分 (1)，高于 500ms 0分
         rtt_score = max(0.0, min(1.0, (500.0 - record.tls_rtt) / (500.0 - 50.0)))

         # --- 综合得分 (加权平均) ---
         # 这里的 0.7 和 0.3 是速度和延迟的权重，可以调整
         record_score = 0.7 * speed_score + 0.3 * (100 * rtt_score) # 将 rtt_score 放大以便于速度比较

         score += record_score * weight
         total_weight += weight

    if total_weight == 0:
        return 0.0

    final_score = score / total_weight
    logger.debug(f"节点 {records[0].node_name} (来自 {records[0].airport_name}) 计算得分: {final_score:.2f} (基于 {len(valid_records)} 条有效记录)")
    return final_score

def calculate_all_scores() -> Dict[str, Dict[str, float]]:
    """
    计算所有商家及其下所有节点的得分。
    返回一个字典，结构：{merchant_name: {node_name: score}}
    """
    logger.info("开始计算所有节点和商家的得分...")
    all_scores = {} # {merchant_id: {node_id: score}}
    node_records = {} # {merchant_id: {node_id: [records]}}

    # 1. 从数据库获取所有最近的记录 (例如最近 30 天)
    # !! 注意：这里需要一个 DAO 函数来获取所有记录或按时间范围获取
    # conn = create_connection()
    # cursor = conn.cursor()
    # thirty_days_ago = datetime.now() - timedelta(days=30)
    # cursor.execute("SELECT * FROM sr_speed_test_record WHERE test_time >= ?", (thirty_days_ago,))
    # rows = cursor.fetchall()
    # close_connection(conn)

    # 假设我们有一个函数能获取所有商家的记录
    # all_merchants = sr_merchant_dao.get_all_merchants() # 需要实现这个 DAO 函数
    # for merchant in all_merchants:
    #     records = ssr_speed_test_record_dao.get_records_by_merchant(merchant.id)

    # !! 简化处理：假设我们能获取所有记录，然后在内存中分组。对于大数据量效率不高 !!
    # all_records = ssr_speed_test_record_dao.get_all_records() # 需要实现这个 DAO 函数
    # 假设 all_records 是 SSRSpeedTestRecord 对象的列表

    # --- 模拟获取记录并分组 ---
    # 这里的实现需要根据你的 DAO 进行调整
    # 假设 `get_all_records_grouped` 返回 {merchant_id: {node_id: [record_obj, ...]}}
    # grouped_records = ssr_speed_test_record_dao.get_all_records_grouped(days=30)

    # --- 临时模拟分组逻辑 (需要替换为 DAO 查询) ---
    print("警告：正在使用模拟数据获取和分组逻辑进行评分，请用真实的 DAO 查询替换！")
    temp_conn = sqlite3.connect('speed_test.db')
    temp_conn.row_factory = sqlite3.Row
    temp_cursor = temp_conn.cursor()
    try:
        temp_cursor.execute("SELECT * FROM sr_speed_test_record WHERE test_time >= date('now', '-30 days')")
        rows = temp_cursor.fetchall()
        all_records_in_30d = []
        for row in rows:
             all_records_in_30d.append(SSRSpeedTestRecord(
                UniqueID=row['id'], airport_id=row['merchant_id'], airport_name=row['merchant_name'],
                node_id=row['node_id'], node_name=row['node_name'], average_speed=row['average_speed'],
                max_speed=row['max_speed'], tls_rtt=row['tls_rtt'], https_delay=row['https_delay'],
                unlock_info=row['unlock_info'], test_time=datetime.fromisoformat(row['test_time']) if row['test_time'] else None,
                insert_time=datetime.fromisoformat(row['gmt_create']) if row['gmt_create'] else None,
                update_time=datetime.fromisoformat(row['gmt_modified']) if row['gmt_modified'] else None,
                host_info=row['host_info']
            ))

        for record in all_records_in_30d:
            if record.airport_id not in node_records:
                node_records[record.airport_id] = {}
            if record.node_id not in node_records[record.airport_id]:
                node_records[record.airport_id][record.node_id] = []
            node_records[record.airport_id][record.node_id].append(record)

    except Exception as e:
         logger.error(f"临时获取评分数据时出错: {e}", exc_info=True)
    finally:
         if temp_conn:
             temp_conn.close()
    # --- 模拟结束 ---


    # 2. 为每个节点计算得分
    merchant_avg_scores = {} # {merchant_id: [node_scores]}
    final_scores_by_name = {} # {merchant_name: {node_name: score}}

    for merchant_id, nodes in node_records.items():
        if merchant_id not in all_scores:
            all_scores[merchant_id] = {}
            merchant_avg_scores[merchant_id] = []

        merchant_name = "未知商家" # 默认值
        merchant_node_scores_by_name = {}

        for node_id, records_list in nodes.items():
            if records_list:
                 node_score = calculate_node_score(records_list)
                 all_scores[merchant_id][node_id] = node_score
                 merchant_avg_scores[merchant_id].append(node_score)
                 # 获取名称用于最终输出
                 node_name = records_list[0].node_name
                 merchant_name = records_list[0].airport_name # 更新商家名称
                 merchant_node_scores_by_name[node_name] = round(node_score, 2)


        if merchant_name != "未知商家":
            # 按得分降序排列节点
             sorted_nodes = dict(sorted(merchant_node_scores_by_name.items(), key=lambda item: item[1], reverse=True))
             final_scores_by_name[merchant_name] = sorted_nodes


    # 3. (可选) 计算商家的平均得分
    merchant_final_scores = {}
    for merchant_id, node_scores in merchant_avg_scores.items():
        if node_scores:
             avg_score = sum(node_scores) / len(node_scores)
             merchant_final_scores[merchant_id] = avg_score
             # logger.info(f"商家 ID {merchant_id} 的平均得分: {avg_score:.2f}")

    logger.info("得分计算完成。")
    # 返回按名称组织的得分，并按商家/节点得分排序
    sorted_merchants = dict(sorted(final_scores_by_name.items(), key=lambda item: sum(item[1].values()) / len(item[1]) if item[1] else 0, reverse=True))

    return sorted_merchants

# --- 示例用法 ---
if __name__ == '__main__':
    # 确保数据库中有数据
    # 需要先运行 main.py 爬取数据
    scores = calculate_all_scores()
    print("\n--- 计算得分结果 ---")
    if scores:
         # 格式化输出
         for merchant, nodes in scores.items():
              avg_m_score = sum(nodes.values()) / len(nodes) if nodes else 0
              print(f"\n{merchant} (平均分: {avg_m_score:.2f})")
              for node, score in nodes.items():
                   print(f"  - {node}: {score:.2f}")
    else:
         print("未能计算任何得分，请检查数据库中是否有足够的数据。")
import sqlite3  # 用于创建内存数据库以加载示例数据

import numpy as np
import pandas as pd

from config import DATABASE_NAME

# --- 0. 准备数据 (模拟从数据库加载) ---
# 使用提供的示例数据创建内存数据库

# SQL DDL 和 DML 语句 (来自用户提供)
sql_statements = """
CREATE TABLE IF NOT EXISTS sr_merchant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gmt_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gmt_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    name TEXT UNIQUE,
    website_url TEXT,
    article_url TEXT,
    article_title TEXT
);

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
);

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
    host_info TEXT
);

-- 插入商户数据 (添加更多商户以供演示)
INSERT INTO "sr_merchant" ("id", "name") VALUES (1, '龙猫云');
INSERT INTO "sr_merchant" ("id", "name") VALUES (2, '一云梯');
INSERT INTO "sr_merchant" ("id", "name") VALUES (7, 'JulangCloud巨浪云');
INSERT INTO "sr_merchant" ("id", "name") VALUES (6, '闪狐云'); -- 假设存在

-- 插入节点数据 (修正 merchant_id 以匹配商户, 添加更多节点)
INSERT INTO "sr_node" ("id", "merchant_id", "merchant_name", "node_name") VALUES (3, 2, '一云梯', '[trojan] 最新网址：1yunti.com');
INSERT INTO "sr_node" ("id", "merchant_id", "merchant_name", "node_name") VALUES (4, 1, '龙猫云', '最新网址：lmspeed.co');
INSERT INTO "sr_node" ("id", "merchant_id", "merchant_name", "node_name") VALUES (5, 7, 'JulangCloud巨浪云', '台湾 - 01');
INSERT INTO "sr_node" ("id", "merchant_id", "merchant_name", "node_name") VALUES (6, 1, '龙猫云', '香港 01');
INSERT INTO "sr_node" ("id", "merchant_id", "merchant_name", "node_name") VALUES (8, 6, '闪狐云', '剩余流量：458.44 GB');
INSERT INTO "sr_node" ("id", "merchant_id", "merchant_name", "node_name") VALUES (11, 1, '龙猫云', '日本 02'); -- 新增节点
INSERT INTO "sr_node" ("id", "merchant_id", "merchant_name", "node_name") VALUES (12, 2, '一云梯', '美国 01'); -- 新增节点
INSERT INTO "sr_node" ("id", "merchant_id", "merchant_name", "node_name") VALUES (13, 2, '一云梯', '新加坡 03'); -- 新增节点 (模拟性能差)


-- 插入测速数据 (使用提供的 JulangCloud 数据, 并添加其他商户/节点的模拟数据)
-- JulangCloud (Node 5, Merchant 7) - 来自用户
INSERT INTO "sr_speed_test_record" ("merchant_id", "merchant_name", "node_id", "node_name", "average_speed", "max_speed", "tls_rtt", "https_delay") VALUES
(7, 'JulangCloud巨浪云', 5, '台湾 - 01', 39.69, 77.75, 61, 493),
(7, 'JulangCloud巨浪云', 5, '台湾 - 01', 7.02, 9.01, 184, 567),
(7, 'JulangCloud巨浪云', 5, '台湾 - 01', 11.29, 25.49, 60, 667),
(7, 'JulangCloud巨浪云', 5, '台湾 - 01', 24.18, 48.98, 276, 1713),
(7, 'JulangCloud巨浪云', 5, '台湾 - 01', 5.25, 9, 74, 1274),
(7, 'JulangCloud巨浪云', 5, '台湾 - 01', 0.074423828125, 0.109375, 323, 2270), -- 速度接近0, 但>0
(7, 'JulangCloud巨浪云', 5, '台湾 - 01', 24.78, 38.23, 182, 1397),
(7, 'JulangCloud巨浪云', 5, '台湾 - 01', 0.155908203125, 0.25, 65, 1610);

-- 龙猫云 (Merchant 1) - 模拟数据
INSERT INTO "sr_speed_test_record" ("merchant_id", "merchant_name", "node_id", "node_name", "average_speed", "max_speed", "tls_rtt", "https_delay") VALUES
(1, '龙猫云', 4, '最新网址：lmspeed.co', 80, 120, 50, 100), -- 节点4 记录1
(1, '龙猫云', 4, '最新网址：lmspeed.co', 90, 130, 45, 90),  -- 节点4 记录2
(1, '龙猫云', 6, '香港 01', 150, 200, 30, 60), -- 节点6 记录1
(1, '龙猫云', 6, '香港 01', 160, 210, 25, 55), -- 节点6 记录2
(1, '龙猫云', 11, '日本 02', 70, 100, 80, 150), -- 节点11 记录1
(1, '龙猫云', 11, '日本 02', 0, 0, NULL, NULL); -- 节点11 记录2 (无效速度)

-- 一云梯 (Merchant 2) - 模拟数据
INSERT INTO "sr_speed_test_record" ("merchant_id", "merchant_name", "node_id", "node_name", "average_speed", "max_speed", "tls_rtt", "https_delay") VALUES
(2, '一云梯', 3, '[trojan] 最新网址：1yunti.com', 100, 150, 60, 110), -- 节点3 记录1
(2, '一云梯', 3, '[trojan] 最新网址：1yunti.com', 110, 160, 55, 105), -- 节点3 记录2
(2, '一云梯', 12, '美国 01', 60, 90, 120, 200), -- 节点12 记录1
(2, '一云梯', 12, '美国 01', 65, 95, 110, 190), -- 节点12 记录2
(2, '一云梯', 13, '新加坡 03', 5, 10, 300, 500), -- 节点13 记录1 (差节点)
(2, '一云梯', 13, '新加坡 03', 8, 12, 280, 480), -- 节点13 记录2 (差节点)
(2, '一云梯', 13, '新加坡 03', 0, 0, 999, 999); -- 节点13 记录3 (无效速度)

-- 闪狐云 (Merchant 6) - 模拟数据 (只有一个节点有测速)
INSERT INTO "sr_speed_test_record" ("merchant_id", "merchant_name", "node_id", "node_name", "average_speed", "max_speed", "tls_rtt", "https_delay") VALUES
(6, '闪狐云', 8, '剩余流量：458.44 GB', 40, 60, 150, 250),
(6, '闪狐云', 8, '剩余流量：458.44 GB', 45, 65, 140, 240);
"""

# 创建内存数据库并执行 SQL
conn = sqlite3.connect(DATABASE_NAME)
cursor = conn.cursor()
# cursor.executescript(sql_statements)
# conn.commit()

# 使用 Pandas 从内存数据库加载数据
merchants_df = pd.read_sql_query("SELECT id, name FROM sr_merchant", conn)
# nodes_df = pd.read_sql_query("SELECT id, merchant_id FROM sr_node", conn) # 暂时不用 nodes_df
speed_tests_df = pd.read_sql_query("SELECT * FROM sr_speed_test_record", conn)
conn.close() # 关闭数据库连接

print("--- 原始测速记录 (部分) ---")
print(speed_tests_df.head())

# --- 1. 数据预处理 ---
print("\n--- 1. 数据预处理 ---")
# 过滤无效记录 (average_speed > 0)
# 同时处理 tls_rtt 和 https_delay 可能的非数字值（虽然表结构是 REAL，以防万一）
numeric_cols = ['average_speed', 'max_speed', 'tls_rtt', 'https_delay']
for col in numeric_cols:
    speed_tests_df[col] = pd.to_numeric(speed_tests_df[col], errors='coerce') # 非数字转为 NaN

valid_tests_df = speed_tests_df[speed_tests_df['average_speed'] > 0].copy()
print(f"有效测速记录数量: {len(valid_tests_df)}")
if len(valid_tests_df) == 0:
    print("没有有效的测速记录，无法进行评分。")
    exit()

# --- 2. 计算节点平均指标 ---
print("\n--- 2. 计算节点平均指标 ---")
# 按 node_id 分组计算平均指标
# .mean() 会自动忽略 NaN 值
node_avg_metrics = valid_tests_df.groupby('node_id').agg(
    # 保留 merchant_id 和 merchant_name 以便后续使用
    merchant_id=('merchant_id', 'first'),
    merchant_name=('merchant_name', 'first'),
    avg_average_speed=('average_speed', 'mean'),
    avg_max_speed=('max_speed', 'mean'),
    avg_tls_rtt=('tls_rtt', 'mean'),
    avg_https_delay=('https_delay', 'mean'),
    record_count=('id', 'count') # 记录有效测试次数
).reset_index()

print("节点平均指标计算结果 (部分):")
print(node_avg_metrics.head())

# --- 3. 指标标准化 ---
print("\n--- 3. 指标标准化 ---")
metrics_to_normalize = ['avg_average_speed', 'avg_max_speed', 'avg_tls_rtt', 'avg_https_delay']
normalized_data = node_avg_metrics.copy()

# 计算全局 min/max (忽略 NaN)
global_min_max = {}
for col in metrics_to_normalize:
    # 只有在列中至少有一个非 NaN 值时才计算 min/max
    if normalized_data[col].notna().any():
        global_min_max[col] = {
            'min': normalized_data[col].min(skipna=True),
            'max': normalized_data[col].max(skipna=True)
            }
    else:
         global_min_max[col] = {'min': np.nan, 'max': np.nan} # 如果全为NaN

# 应用标准化
for col in metrics_to_normalize:
    norm_col_name = f'norm_{col}'
    min_val = global_min_max[col]['min']
    max_val = global_min_max[col]['max']

    # 检查 min/max 是否有效 (非 NaN)
    if pd.isna(min_val) or pd.isna(max_val):
         normalized_data[norm_col_name] = np.nan # 如果无法计算 min/max，则标准化结果为 NaN
         print(f"警告: 指标 {col} 的全局 min/max 无法计算 (可能所有值都为 NaN)，标准化得分设为 NaN。")
         continue

    # 避免除以零
    if max_val == min_val:
        # 如果所有节点的这个指标值都一样，给一个中性分数 0.5
        # 但要确保原始值不是 NaN
        normalized_data[norm_col_name] = np.where(normalized_data[col].isna(), np.nan, 0.5)
    else:
        normalized_data[norm_col_name] = (normalized_data[col] - min_val) / (max_val - min_val)

# 翻转延迟/RTT指标 (值越低越好 -> 分数越高越好)
# 注意: 1 - NaN = NaN，行为符合预期
normalized_data['norm_tls_rtt_score'] = 1 - normalized_data['norm_avg_tls_rtt']
normalized_data['norm_https_delay_score'] = 1 - normalized_data['norm_avg_https_delay']

print("\n标准化后的节点指标 (部分):")
# 选择要显示的标准化后列
display_cols = ['node_id', 'merchant_id', 'norm_avg_average_speed', 'norm_avg_max_speed', 'norm_tls_rtt_score', 'norm_https_delay_score']
print(normalized_data[display_cols].head())

# --- 4. 计算节点综合得分 ---
print("\n--- 4. 计算节点综合得分 ---")
# 定义权重
weights = {
    'avg_speed': 0.3,
    'max_speed': 0.1,
    'tls_rtt': 0.2,
    'https_latency': 0.4
}

# 计算加权得分
# 使用 .fillna(0) 处理标准化步骤中可能产生的 NaN 值。
# 这意味着如果一个节点的某个指标无法标准化（如所有测速都是 NULL），该指标对总分的贡献为 0。
# 你也可以选择其他策略，比如如果任一指标为 NaN，则总分为 NaN。
normalized_data['node_score'] = (
    weights['avg_speed'] * normalized_data['norm_avg_average_speed'].fillna(0) +
    weights['max_speed'] * normalized_data['norm_avg_max_speed'].fillna(0) +
    weights['tls_rtt'] * normalized_data['norm_tls_rtt_score'].fillna(0) +
    weights['https_latency'] * normalized_data['norm_https_delay_score'].fillna(0)
)

# 将得分限制在 0-1 之间 (理论上加权和应该在 0-1，保险起见)
normalized_data['node_score'] = normalized_data['node_score'].clip(0, 1)

print("\n计算得到的节点得分 (部分):")
print(normalized_data[['node_id', 'merchant_id', 'merchant_name', 'record_count', 'node_score']].head())

# --- 5. 计算商户得分 (使用 P75 百分位数) ---
print("\n--- 5. 计算商户得分 (P75 百分位数) ---")

# 按 merchant_id 分组，计算 node_score 的 75% 分位数
# quantile() 默认会忽略 NaN 值
merchant_scores_p75 = normalized_data.groupby('merchant_id')['node_score'].quantile(0.75).reset_index()
merchant_scores_p75.rename(columns={'node_score': 'merchant_score_p75'}, inplace=True)

# (可选) 计算平均分作为对比
merchant_scores_avg = normalized_data.groupby('merchant_id')['node_score'].mean().reset_index()
merchant_scores_avg.rename(columns={'node_score': 'merchant_score_avg'}, inplace=True)

# (可选) 计算节点数量
merchant_node_counts = normalized_data.groupby('merchant_id')['node_id'].nunique().reset_index()
merchant_node_counts.rename(columns={'node_id': 'scored_node_count'}, inplace=True)


# 合并结果到原始商户表
final_scores = pd.merge(merchants_df, merchant_scores_p75, on='merchant_id', how='left')
final_scores = pd.merge(final_scores, merchant_scores_avg, on='merchant_id', how='left')
final_scores = pd.merge(final_scores, merchant_node_counts, on='merchant_id', how='left')

# 使用商户名进行合并，以处理可能不在 merchants_df 中的商户 (如果 speed_tests 直接用了名字)
# 或者确保 merchants_df 包含所有出现在 speed_tests 中的 merchant_id
# 这里我们假设 merchants_df 包含了所有相关的 merchant_id

# 填充 NaN 得分 (例如，如果一个商户没有任何有效节点评分)
final_scores[['merchant_score_p75', 'merchant_score_avg']] = final_scores[['merchant_score_p75', 'merchant_score_avg']].fillna(0)
final_scores['scored_node_count'] = final_scores['scored_node_count'].fillna(0).astype(int)


print("\n--- 最终商户得分 ---")
# 按 P75 得分降序排列
final_scores_sorted = final_scores.sort_values(by='merchant_score_p75', ascending=False).reset_index(drop=True)
print(final_scores_sorted)

print(f"""
代码执行完毕。
- 读取了 sr_merchant 和 sr_speed_test_record 的数据。
- 过滤了 average_speed <= 0 的无效测速记录。
- 计算了每个节点的平均速度、最大速度、TLS RTT 和 HTTPS 延迟。
- 对这些平均指标进行了全局 Min-Max 标准化 (0-1范围，越高越好)。
- 根据权重计算了每个节点的综合得分 (node_score)。
- 计算了每个商户所有节点得分的 75% 分位数 (P75) 和平均分，并统计了参与评分的节点数。
- 将结果合并显示，并按 P75 得分排序。
""")

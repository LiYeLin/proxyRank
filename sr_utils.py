import logging

import pandas as pd

from config import REQUIRED_KEYS

logger = logging.getLogger(__name__)

def parse_speed(speed_str):
    if not speed_str: return None
    # 简单处理：去除单位，转换为 float (假设单位是 Mbps)
    trim_str = str(speed_str).replace(' ', '')
    num, unit = trim_str[:-2], trim_str[-2:].upper()
    # 将数字转为浮点数
    try:
        num = float(num)
    except ValueError:
        return 0.0
    # 根据单位进行转换
    if unit == "MB":
        return num
    elif unit == "KB":
        return num / 1024
    elif unit == "GB":
        return num * 1024
    elif unit == "TB":
        return num * 1024 * 1024
    else:
        return 0.0  # 对于未知单位或 B（字节），返回 0.0

def validate_data(llm_result: dict) -> bool:
    """验证数据是否满足所有字段非空 (改进版)"""

    # 检查 test_record_list 本身是否存在且非空列表
    if "test_record_list" not in llm_result or not isinstance(llm_result["test_record_list"], list):
        logger.error("Validation failed: 'test_record_list' key is missing or not a list.")
        return False

    test_records = llm_result["test_record_list"]

    if not test_records:
         return True

    for i, data in enumerate(test_records):
        if not isinstance(data, dict): # 确保列表中的每个元素都是字典
            print(f"大模型返回验证失败: Item at index {i} is not a dictionary.")
            return False

        # 更好的键名标准化 (示例，假设 normalize_key 是正确的)
        normalized_data = {}
        # 使用 list(data.items()) 避免在迭代时修改引发潜在问题
        for key, value in list(data.items()):
             normalized_key = normalize_key(key) # 依赖外部 normalize_key
             normalized_data[normalized_key] = value # 创建新的标准化字典

        # 检查必需字段是否存在且值非空（更精确的非空判断）
        for required_key in REQUIRED_KEYS:
            # 对标准化后的字典进行检查
            if required_key not in normalized_data:
                logger.error(f"大模型返回验证失败: 第{i}行缺少'{required_key}'字段 .")
                return False

            value = normalized_data[required_key]

            # 非空判断
            is_empty = False
            if value is None:
                is_empty = True
            elif isinstance(value, str) and not value.strip(): # 检查空字符串或只有空格的字符串
                is_empty = True
            # 注意：对于数值类型，0 或 0.0 不是空的。但 np.nan 或 pd.isna(value) 是空的。
            elif isinstance(value, (int, float)) and pd.isna(value):
                 is_empty = True
            # 如果还有其他类型需要判断空，例如列表或字典
            elif isinstance(value, (list, dict)) and not value:
                 is_empty = True

            if is_empty:
                logger.error(f"大模型返回验证失败: 第{i}行数据中飞空的字段值为空 '{required_key}'")
                return False
    return True
def filter_valid_records(llm_result: dict) -> dict:
    """
    从 LLM 返回的结果中过滤并返回满足所有必需字段存在且值非空要求的记录。

    Args:
        llm_result: 从 LLM 返回的字典结果，期望包含 'test_record_list' 键。

    Returns:
        一个只包含有效记录字典的新列表 (键已标准化)。
        如果输入数据结构不正确或列表为空，返回空列表。
    """
    valid_records = [] # 创建一个空列表，用于存放所有符合要求的记录

    # 检查 test_record_list 本身是否存在且是列表
    # 使用 .get() 更安全，避免在外层直接访问不存在的键时报错
    test_records = llm_result.get("test_record_list")

    # 如果键缺失、值不是列表、或者列表为空，则没有记录需要验证，直接返回空列表
    if not isinstance(test_records, list) or not test_records:
         # 区分是键缺失还是列表为空进行更详细的日志
        if "test_record_list" not in llm_result or test_records is None:
             logger.error("Filtering skipped: Input 'test_record_list' key is missing or None.")
        elif not isinstance(test_records, list):
             logger.error("Filtering skipped: Value for 'test_record_list' is not a list.")
        else: # test_records is an empty list []
             logger.info("'test_record_list' is empty. Returning empty list.")

        return [] # 返回空列表，因为没有有效的记录可以提取


    # 遍历每一条记录进行验证和过滤
    original_count = len(test_records) # 记录原始数量
    for i, data in enumerate(test_records):
        # 1. 检查当前元素是否是字典
        if not isinstance(data, dict):
            logger.warning(f"Filtering record at index {i}: Item is not a dictionary ({type(data).__name__}), skipping.")
            continue # 跳过这个不符合类型要求的元素，处理下一个

        # 2. 键名标准化 - 创建一个新的字典，而不是修改原始字典
        normalized_data = {}
        # 使用 list(data.items()) 可以在极少数情况下，即使在迭代时字典发生意外变动也能保证安全
        # 但更主要的原因是我们正在构建一个新的字典
        for key, value in data.items():
             # 假设 normalize_key 总是返回字符串并且能处理各种输入键类型
             try:
                 normalized_key = normalize_key(key) # 依赖外部 normalize_key
                 normalized_data[normalized_key] = value # 将原始值赋给新的标准化键
             except Exception as e:
                  # 如果 normalize_key 本身出错，跳过此条记录
                  logger.warning(f"Filtering record at index {i}: Error during key normalization for key '{key}', skipping item. Error: {e}")
                  normalized_data = None # 标记此条记录因标准化失败而无效
                  break # 标准化失败，无需继续检查此条记录的必需字段

        if normalized_data is None: # 检查上面标准化过程中是否失败
            continue # 标准化失败的记录已记录日志，跳过

        # 3. 检查必需字段是否存在且值非空
        is_item_valid = True # 标记当前记录是否符合要求，默认认为有效
        failed_reason = None # 用于记录失败原因

        for required_key in REQUIRED_KEYS:
            # 检查必需键是否存在于标准化后的字典中
            if required_key not in normalized_data:
                failed_reason = f"missing required field '{required_key}'"
                is_item_valid = False # 当前记录不符合要求
                break # 找到第一个不符合的必需字段，无需检查其他，跳出 inner loop

            value = normalized_data[required_key]

            # 非空判断 (使用您原有的逻辑)
            is_empty = False
            if value is None:
                is_empty = True
            elif isinstance(value, str) and not value.strip(): # 检查 None, 空字符串, 只含空格的字符串
                is_empty = True
            # 判断数值类型的 NaN (Not a Number)
            # 使用 pandas.isna() 是一种方法，需要导入 pandas
            # 如果不想依赖 pandas，对于 float 类型可以使用 value != value 来判断 NaN
            elif isinstance(value, float):
                 # Check for NaN specifically
                 # if pd.isna(value): # Option 1: Requires pandas
                 if value != value: # Option 2: Pure Python way to check float NaN
                      is_empty = True
            # 判断空的列表 [] 或空的字典 {}
            elif isinstance(value, (list, dict)) and not value:
                 is_empty = True

            if is_empty:
                # 必需字段存在，但其值根据非空判断规则视为空
                # 限制一下打印的值的长度，避免日志过长
                display_value = str(value)
                if len(display_value) > 50:
                    display_value = display_value[:47] + "..."
                failed_reason = f"field '{required_key}' has an empty value ('{display_value}')"
                is_item_valid = False # 当前记录不符合要求
                break # 找到第一个值为空的必需字段，无需检查其他，跳出 inner loop

        # 4. 如果当前记录通过了所有必需字段的检查 (is_item_valid 仍然是 True)
        if is_item_valid:
            valid_records.append(normalized_data) # 将经过标准化处理的字典添加到结果列表
        else:
            # 如果记录不符合要求，记录日志说明原因
            logger.warning(f"Filtering record at index {i}: Skipped because {failed_reason}.")


    logger.info(f"Original number of records processed: {original_count}. Filtered valid records: {len(valid_records)}.")
    llm_result["test_record_list"]  = valid_records
    return llm_result # 返回收集到的所有有效记录的列表

def normalize_key(key: str) -> str:
    """去除键名中的空格并标准化"""
    return key.replace(" ", "")


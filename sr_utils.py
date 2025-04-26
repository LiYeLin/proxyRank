from config import REQUIRED_KEYS


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
    """验证数据是否满足所有字段非空"""
    # 第一步：标准化所有键名（去除空格）
    for data in llm_result.get("test_record_list",[]):
        for key, value in data.items():
            new_key = normalize_key(key)
            data[new_key] = value

        # 第二步：检查必需字段是否存在且值非空
        for required_key in REQUIRED_KEYS:
            if required_key not in data:
                return False
            value = data[required_key]
            if not value:  # 检查空值（None, 空字符串, 空列表等）
                return False
    return True
def normalize_key(key: str) -> str:
    """去除键名中的空格并标准化"""
    return key.replace(" ", "")


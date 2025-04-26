from models.SRNode import SRNode
from models.SSRSpeedTestRecord import SSRSpeedTestRecord
from sr_utils import parse_speed


def ocr_convert_to_record(ocr_record: dict, merchant_id: int, test_time: str, merchant_name: str,pic_info:dict) -> list | None:
    # -- 从 OCR 结果中提取关键字段 --
    node_name_raw = ocr_record.get("节点名称")
    avg_speed_str = ocr_record.get("平均速度")
    max_speed_str = ocr_record.get("最高速度")
    tls_rtt_str = ocr_record.get("TLS RTT") or ocr_record.get("TLSRTT")
    https_delay_str = ocr_record.get("HTTPS 延迟") or ocr_record.get("HTTPS延迟")
    type = ocr_record.get("类型")

    if not all([node_name_raw, avg_speed_str, max_speed_str, tls_rtt_str, https_delay_str]):
        raise ValueError(f"OCR 缺少数据:ocr: {ocr_record}")

    # 清理和转换数据
    node_name = node_name_raw.strip()
    avg_speed = parse_speed(avg_speed_str)
    max_speed = parse_speed(max_speed_str)
    tls_rtt = tls_rtt_str[:-2]
    https_delay = https_delay_str[:-2]
    record = SSRSpeedTestRecord(airport_id=merchant_id, airport_name=merchant_name, node_name=node_name,
                                average_speed=avg_speed, max_speed=max_speed, tls_rtt=tls_rtt, https_delay=https_delay,
                                test_time=test_time, host_info=None,pic_id = pic_info.get("pic_id"))
    sr_node = SRNode(node_name=node_name, type=type, merchant_id=merchant_id, merchant_name=merchant_name)
    return [sr_node, record]

from dataclasses import dataclass


# 实体类
@dataclass
class SSRSpeedTestRecord:
    def __init__(self, UniqueID=None, airport_id=None, airport_name=None, node_id=None, node_name=None,
                 average_speed=None, max_speed=None, tls_rtt=None, https_delay=None, unlock_info=None,
                 test_time=None, insert_time=None, update_time=None, host_info=None):
        self.UniqueID = UniqueID
        self.airport_id = airport_id
        self.airport_name = airport_name
        self.node_id = node_id
        self.node_name = node_name
        self.average_speed = average_speed
        self.max_speed = max_speed
        self.tls_rtt = tls_rtt
        self.https_delay = https_delay
        self.unlock_info = unlock_info
        self.test_time = test_time
        self.insert_time = insert_time
        self.update_time = update_time
        self.host_info = host_info

    def __repr__(self):
        return f"<SSRSpeedTestRecord id={self.UniqueID} airport='{self.airport_name}' node='{self.node_name}'>"

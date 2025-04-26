
class SRNode:
    def __init__(self, node_id=None, node_name=None, type=None, merchant_id=None, merchant_name=None):
        self.node_id = node_id
        self.node_name = node_name
        self.type = type
        self.merchant_id = merchant_id
        self.merchant_name = merchant_name

    def __repr__(self):
        return f"<SRNode id={self.node_id} name='{self.node_name}'>"
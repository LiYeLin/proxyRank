
class SRNode:
    def __init__(self, node_id=None, node_name=None, type=None, region=None):
        self.node_id = node_id
        self.node_name = node_name
        self.type = type
        self.region = region

    def __repr__(self):
        return f"<SRNode id={self.node_id} name='{self.node_name}'>"
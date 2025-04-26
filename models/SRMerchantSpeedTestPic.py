
class SRMerchantSpeedTestPic:
    def __init__(self, id=None, merchant_id=None, pic_md5=None, pic_url=None, pic_path=None, test_time=None,model_return=None):
        self.id = id
        self.merchant_id = merchant_id
        self.pic_md5 = pic_md5
        self.pic_url = pic_url
        self.pic_path = pic_path
        self.test_time = test_time
        self.model_return = model_return

    def __repr__(self):
        return f"<SRMerchantSpeedTestPic id={self.id} pic_url='{self.pic_url}'>"

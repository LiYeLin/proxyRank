
class SRMerchant:
    def __init__(self, id=None, name=None, website_url=None, article_url=None, article_title=None):
        self.id = id
        self.name = name
        self.website_url = website_url
        self.article_url = article_url
        self.article_title = article_title

    def __repr__(self):
        return f"<SRMerchant id={self.id} name='{self.name}'>"

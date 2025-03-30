from dataclasses import dataclass
from datetime import datetime


@dataclass
class articleInfo:
    articleTitle: str
    articleText:str
    articleUrl: str
    articleImages: list
    articleDateTime:datetime
    htmlContent:str

    def to_dict(self):
        return {
            "articleTitle": self.articleTitle,
            "articleText": self.articleText,
            "articleUrl": self.articleUrl,
            "articleImages": self.articleImages,
            "articleDateTime": self.articleDateTime.strftime("%Y-%m-%d %H:%M:%S"),
            "htmlContent": self.htmlContent
        }
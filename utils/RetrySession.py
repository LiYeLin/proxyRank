import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class RetrySession:
    def __init__(self, total_retries=3, backoff_factor=0.5, status_forcelist=None, allowed_methods=None):
        """
        创建一个带有重试机制的 requests Session。

        Args:
            total_retries (int): 最大重试次数。
            backoff_factor (float): 退避因子，用于计算重试之间的延迟。
                                     延迟时间 = backoff_factor * (2 ** (重试次数 - 1))
            status_forcelist (set): 需要强制重试的 HTTP 状态码集合，默认为 None。
            allowed_methods (set): 允许重试的 HTTP 方法集合，默认为 None (即所有方法都允许重试)。
        """
        if status_forcelist is None:
            status_forcelist = {429, 500, 502, 503, 504}
        if allowed_methods is None:
            allowed_methods = {'HEAD', 'GET', 'PUT', 'DELETE', 'OPTIONS', 'TRACE', 'POST'}  # POST 通常不建议自动重试，除非你知道其幂等性

        retry = Retry(
            total=total_retries,
            read=total_retries,
            connect=total_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=allowed_methods
        )

        self.http = requests.Session()
        adapter = HTTPAdapter(max_retries=retry)
        self.http.mount("http://", adapter)
        self.http.mount("https://", adapter)

    def get(self, url, **kwargs):
        return self.http.get(url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.http.post(url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.http.put(url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        return self.http.delete(url, **kwargs)

    def head(self, url, **kwargs):
        return self.http.head(url, **kwargs)

    def options(self, url, **kwargs):
        return self.http.options(url, **kwargs)
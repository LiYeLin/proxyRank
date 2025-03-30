from urllib.parse import urlparse


def is_valid_url(url):
    try:
        result = urlparse(url)
        return bool(result.scheme or result.netloc)
    except ValueError:
        return False

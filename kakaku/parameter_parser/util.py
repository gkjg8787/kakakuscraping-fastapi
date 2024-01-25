from urllib.parse import urlparse
from common.read_config import get_support_url


def is_suppoer_url(url_path: str) -> bool:
    if not url_path:
        return False
    sulist = get_support_url().values()
    up = urlparse(url_path)
    if up.netloc in sulist:
        return True
    return False


def is_valid_id(num: str) -> bool:
    if num and num.isdigit() and int(num) >= 0:
        return True
    return False

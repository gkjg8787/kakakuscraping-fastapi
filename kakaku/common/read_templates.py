from fastapi.templating import Jinja2Templates


from urllib.parse import urlparse

from common.read_config import get_support_url, get_allow_unsupported_links_in_html
from common.util import isLocalToday

templates = Jinja2Templates(directory="templates")


def isSupportDomain(urlpath) -> bool:
    if get_allow_unsupported_links_in_html():
        return True
    suplist = get_support_url().values()
    parsed_url = urlparse(urlpath)
    if parsed_url.netloc in suplist:
        return True
    return False


def isLowestPrice(price, lowestprice) -> bool:
    try:
        if int(price) - int(lowestprice) <= 100 or ((price / lowestprice) - 1) <= 0:
            return True
        return False
    except Exception:
        return False


templates.env.filters["isSupportDomain"] = isSupportDomain
templates.env.filters["isLowestPrice"] = isLowestPrice
templates.env.filters["isLocalToday"] = isLocalToday

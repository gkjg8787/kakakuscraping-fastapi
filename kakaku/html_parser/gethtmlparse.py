from urllib.parse import urlparse
from datetime import datetime

from html_parser import (
    surugaya_html_parse,
    netoff_html_parse,
    bookoff_html_parse,
    htmlparse,
)
from common.read_config import get_support_url, ItemParseOptions


def getParser(
    filepath: str,
    url_id: int,
    date: datetime,
    url: str,
    itemparseoptions: ItemParseOptions,
) -> htmlparse.ParseItems | None:
    fp = open(filepath, encoding="utf-8")
    parsed_url = urlparse(url)
    supdict = get_support_url()
    if "surugaya" in supdict and supdict["surugaya"] == parsed_url.netloc:
        return surugaya_html_parse.SurugayaParse(
            fp, url_id, date, url, itemparseoptions
        )

    if "netoff" in supdict and supdict["netoff"] == parsed_url.netloc:
        return netoff_html_parse.NetoffParse(fp, url_id, date, url)

    if "bookoff" in supdict and supdict["bookoff"] == parsed_url.netloc:
        return bookoff_html_parse.BookoffParse(fp, url_id, date, url)

    return None

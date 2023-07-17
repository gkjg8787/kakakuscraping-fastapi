from urllib.parse import urlparse

from html_parser import (
    surugaya_html_parse,
    netoff_html_parse,
    bookoff_html_parse,
    geo_html_parse,
)

def getParser(filepath, url_id, date, url):
    fp = open(filepath, encoding="utf-8")
    parsed_url = urlparse(url)
    if "www.suruga-ya.jp" == parsed_url.netloc:
        return surugaya_html_parse.SurugayaParse(fp, url_id, date, url)
    
    if "www.netoff.co.jp" == parsed_url.netloc:
        return netoff_html_parse.NetoffParse(fp, url_id, date, url)

    if "www.bookoffonline.co.jp" == parsed_url.netloc:
        return bookoff_html_parse.BookoffParse(fp, url_id, date, url)

    if 'ec.geo-online.co.jp' == parsed_url.netloc:
        return geo_html_parse.GeoParse(fp, url_id, date, url)

    return None
    

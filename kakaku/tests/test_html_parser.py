from downloader import download_html as dl

from html_parser import (
    bookoff_html_parse,
)


def test_bookoff_html_parser():
    url = "https://shopping.bookoff.co.jp/used/0010467610"
    title = 'ハウルの動く城'
    retb, text = dl.getUrlHtml(url=url)
    assert retb == True
    assert len(text) > 0
    bk = bookoff_html_parse.BookoffParse(text, id=1, date='2023-01-01 00:00:00', url=url)
    ret = bk.getItems()
    for r in ret:
        print(r.getOrderedDict())
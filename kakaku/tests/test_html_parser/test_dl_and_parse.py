from downloader import download_html as dl

from html_parser import (
    bookoff_html_parse,
    surugaya_html_parse,
)


def test_bookoff_dl_and_parse():
    url = "https://shopping.bookoff.co.jp/used/0010467610"
    title = 'ハウルの動く城'
    retb, text = dl.getUrlHtml(url=url)
    assert retb == True
    assert len(text) > 0
    bk = bookoff_html_parse.BookoffParse(text, id=1, date='2023-01-01 00:00:00', url=url)
    ret = bk.getItems()
    for r in ret:
        print(r.getOrderedDict())

def test_surugaya_html_dl_and_parse_product_other():
    url = "https://www.suruga-ya.jp/product/other/128006258"
    title = "天空の城ラピュタ"
    retb, text = dl.getUrlHtml(url=url)
    assert retb == True
    assert len(text) > 0
    bk = surugaya_html_parse.SurugayaParse(text, id=1, date='2023-01-01 00:00:00', url=url)
    ret = bk.getItems()
    for r in ret:
        print(r.getOrderedDict())

def test_surugaya_dl_and_parse_product_detail():
    url = "https://www.suruga-ya.jp/product/detail/128022745"
    title = "ゲド戦記"
    retb, text = dl.getUrlHtml(url=url)
    assert retb == True
    assert len(text) > 0
    bk = surugaya_html_parse.SurugayaParse(text, id=1, date='2023-01-01 00:00:00', url=url)
    ret = bk.getItems()
    for r in ret:
        print(r.getOrderedDict())
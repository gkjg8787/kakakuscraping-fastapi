import os

from html_parser import netoff_search

search_fpath = os.path.dirname(__file__) + "/data/netoff_search.html"


def assert_has_keys(required_keys: list, target_dict: dict):
    for k in required_keys:
        assert k in target_dict.keys()


def assert_item(item: dict[str], correct: dict[str, str]):
    for k in correct.keys():
        if type(item[k]) is str:
            assert item[k].strip() == correct[k]
        else:
            assert item[k] == correct[k]


def test_netoff_search():
    corrects = [
        {
            "storename": "ネットオフ",
            "title": "Focus on“ONE PIECE FAN LETTER”",
            "titleURL": "https://www.netoff.co.jp/detail/0014086755/",
            "imageOnError": "https://www.netoff.co.jp/ebimage/noimage_comic_01.gif",
            "category": "古本・中古本",
            "price": "1,150円",
            "imageURL": "https://www.netoff.co.jp/ebimage/noimage_book_01.gif",
        },
        {
            "storename": "ネットオフ",
            "title": "ワンピース・マガジン＜019＞",
            "titleURL": "https://www.netoff.co.jp/detail/0014021548/",
            "imageOnError": "https://www.netoff.co.jp/ebimage/noimage_comic_01.gif",
            "category": "古本・中古本",
            "price": "990円",
            "imageURL": "https://www.netoff.co.jp/ebimage/cmdty/0014021548.jpg",
        },
    ]
    with open(search_fpath, encoding="utf-8") as fp:
        sp = fp.read()
    ss = netoff_search.SearchNetoff()
    ss.parseSearch(sp)
    items_required_key_list = [
        "storename",
        "title",
        "titleURL",
        "category",
        # "used_price",
        # "sinagire",
        "imageURL",
    ]
    for item_dict in ss.getItems():
        assert_has_keys(items_required_key_list, item_dict)
        print(item_dict)

    assert_item(item=ss.getItems()[0], correct=corrects[0])
    assert_item(item=ss.getItems()[6], correct=corrects[1])

    pages_required_key_list = ["enable", "min", "max"]
    page = ss.getPage()
    assert_has_keys(pages_required_key_list, page)
    assert page["enable"] == "true"
    assert page["min"] == 1
    assert page["max"] == 5
    assert page["more"] == "true"

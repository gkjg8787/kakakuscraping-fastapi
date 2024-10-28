import os

from html_parser import surugaya_search

search_fpath = os.path.dirname(__file__) + "/data/surugaya_search_marika.html"


def assert_has_keys(required_keys: list, target_dict: dict) -> bool:
    for k in required_keys:
        assert k in target_dict.keys()


def test_surugaya_search():
    corrects = [
        {
            "storename": "駿河屋",
            "title": "マリオカート8 デラックス + コース追加パス",
            "titleURL": "https://www.suruga-ya.jp/product/detail/109003254",
            "category": "ニンテンドースイッチソフト",
            "used_price": "中古：￥8,800税込",
            "makepure": "￥8,280",
            "makepurebiko": "(8点の中古品)",
            "makepureURL": "https://www.suruga-ya.jp/product/other/109003254",
            "imageURL": "https://www.suruga-ya.jp/database/photo.php?shinaban=109003254&size=m",
        }
    ]
    with open(search_fpath, encoding="utf-8") as fp:
        sp = fp.read()
    ss = surugaya_search.SearchSurugaya()
    ss.parseSearch(sp)
    items_required_key_list = [
        "storename",
        "title",
        "titleURL",
        "category",
        # "used_price",
        # "makepure",
        # "makepurebiko",
        # "makepureURL",
        # "sinagire",
        "imageURL",
    ]
    for item_dict in ss.getItems():
        assert_has_keys(items_required_key_list, item_dict)
        print(item_dict)

    one = ss.getItems()[0]
    correct_one = corrects[0]
    for k in correct_one.keys():
        if type(one[k]) is str:
            assert one[k].strip() == correct_one[k]
        else:
            assert one[k] == correct_one[k]

    pages_required_key_list = ["enable", "min", "max"]
    page = ss.getPage()
    assert_has_keys(pages_required_key_list, page)
    assert page["enable"] == "true"
    assert page["min"] == 1
    assert page["max"] == 4


def test_surugaya_search_range_usedprice():
    corrects = [
        {
            "storename": "駿河屋",
            "title": "マリオカート ライブ ホームサーキット マリオセット",
            "titleURL": "https://www.suruga-ya.jp/product/detail/109102234",
            "category": "ニンテンドースイッチハード",
            "used_price": "中古：￥3,440～￥4,300税込",
            "makepure": "￥3,040",
            "makepurebiko": "(11点の中古品)",
            "makepureURL": "https://www.suruga-ya.jp/product/other/109102234",
            "imageURL": "https://www.suruga-ya.jp/database/photo.php?shinaban=109102234&size=m",
        }
    ]
    with open(search_fpath, encoding="utf-8") as fp:
        sp = fp.read()
    ss = surugaya_search.SearchSurugaya()
    ss.parseSearch(sp)

    one = ss.getItems()[1]
    correct_one = corrects[0]
    for k in correct_one.keys():
        if type(one[k]) is str:
            assert one[k].strip() == correct_one[k]
        else:
            assert one[k] == correct_one[k]

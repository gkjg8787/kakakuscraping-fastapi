from html_parser import surugaya_search
from .read_data import read_tgz

search_fpath = "surugaya_search_marika.html"
search_detail_direct_fpath = "surugaya_search_mononoke_detail_direct.html"


def assert_has_keys(required_keys: list, target_dict: dict):
    for k in required_keys:
        assert k in target_dict.keys()


def assert_item(item: dict[str], correct: dict[str, str]):
    for k in correct.keys():
        if type(item[k]) is str:
            assert item[k].strip() == correct[k]
        else:
            assert item[k] == correct[k]


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
    sp = read_tgz(search_fpath)
    ss = surugaya_search.SearchSurugaya(is_converturl=True)
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

    assert_item(item=ss.getItems()[0], correct=corrects[0])

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
    sp = read_tgz(search_fpath)
    ss = surugaya_search.SearchSurugaya(is_converturl=True)
    ss.parseSearch(sp)

    assert_item(item=ss.getItems()[1], correct=corrects[0])


def test_surugaya_search_detail_direct():
    corrects = [
        {
            "storename": "駿河屋",
            "title": "もののけ姫",
            "titleURL": "https://www.suruga-ya.jp/product/detail/428046271",
            "category": "アニメBlu-rayDisc",
            "used_price": "中古：￥4,800税込",
            "makepure": "￥3,520",
            "makepurebiko": "(7点の中古品)",
            "makepureURL": "https://www.suruga-ya.jp/product/other/428046271",
            "imageURL": "https://www.suruga-ya.jp/database/photo.php?shinaban=428046271&size=m",
        },
        {},
        {
            "storename": "駿河屋",
            "title": "もののけ姫",
            "titleURL": "https://www.suruga-ya.jp/product/detail/128049960",
            "category": "アニメDVD",
            "sinagire": "品切れ",
            "makepure": "￥2,950",
            "makepurebiko": "(1点の中古品)",
            "makepureURL": "https://www.suruga-ya.jp/product/other/128049960",
            "imageURL": "https://www.suruga-ya.jp/database/photo.php?shinaban=128049960&size=m",
        },
    ]
    sp = read_tgz(search_detail_direct_fpath)
    ss = surugaya_search.SearchSurugaya(is_converturl=True)
    ss.parseSearch(sp)
    items_required_key_list = [
        "storename",
        "title",
        "titleURL",
        "category",
        "imageURL",
    ]
    for item_dict in ss.getItems():
        assert_has_keys(items_required_key_list, item_dict)

    assert_item(item=ss.getItems()[0], correct=corrects[0])
    assert_item(item=ss.getItems()[2], correct=corrects[2])

    pages_required_key_list = ["enable", "min", "max"]
    page = ss.getPage()
    assert_has_keys(pages_required_key_list, page)
    assert page["enable"] == "true"
    assert page["min"] == 1
    assert page["max"] == 3


def test_surugaya_search_detail_direct_not_converturl():
    corrects = [
        {
            "storename": "駿河屋",
            "title": "もののけ姫",
            "titleURL": "https://www.suruga-ya.jp/product/detail/428046271",
            "category": "アニメBlu-rayDisc",
            "used_price": "中古：￥4,800税込",
            "makepure": "￥3,520",
            "makepurebiko": "(7点の中古品)",
            "makepureURL": "https://www.suruga-ya.jp/product/other/428046271",
            "imageURL": "https://www.suruga-ya.jp/database/photo.php?shinaban=428046271&size=m",
        },
        {},
        {
            "storename": "駿河屋",
            "title": "もののけ姫",
            "titleURL": "https://www.suruga-ya.jp/product/detail/128049960?tenpo_cd=400506",
            "category": "アニメDVD",
            "sinagire": "品切れ",
            "makepure": "￥2,950",
            "makepurebiko": "(1点の中古品)",
            "makepureURL": "https://www.suruga-ya.jp/product/detail/128049960?tenpo_cd=400506",
            "imageURL": "https://www.suruga-ya.jp/database/photo.php?shinaban=128049960&size=m",
        },
    ]
    sp = read_tgz(search_detail_direct_fpath)
    ss = surugaya_search.SearchSurugaya(is_converturl=False)
    ss.parseSearch(sp)
    items_required_key_list = [
        "storename",
        "title",
        "titleURL",
        "category",
        "imageURL",
    ]
    for item_dict in ss.getItems():
        assert_has_keys(items_required_key_list, item_dict)

    assert_item(item=ss.getItems()[0], correct=corrects[0])
    assert_item(item=ss.getItems()[2], correct=corrects[2])

    pages_required_key_list = ["enable", "min", "max"]
    page = ss.getPage()
    assert_has_keys(pages_required_key_list, page)
    assert page["enable"] == "true"
    assert page["min"] == 1
    assert page["max"] == 3

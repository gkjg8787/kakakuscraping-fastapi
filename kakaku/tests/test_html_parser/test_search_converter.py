from html_parser.search_converter import (
    SearchDictConverter,
    SearchResultItem,
    SearchResultPage,
    MainItem,
)
from html_parser.search_parser import SearchParser, SearchCmn
from common.filter_name import FilterQueryName

netoff_img_on_err = "https://st.netoff.co.jp/ebimage/noimage_comic_01.gif"
bookoff_img_on_err = "https://content.bookoffonline.co.jp/images/goods/item_l.gif"


def test_convertToSearchResultItems_full():
    items_dict = {
        "surugaya1": {
            SearchParser.STORENAME: "駿河屋",
            SearchParser.IMAGE_URL: "https://www.suruga-ya.jp/database/photo.php?shinaban=109000860&size=m",
            SearchParser.TITLE: "ポケモン不思議のダンジョン 救助隊DX",
            SearchParser.TITLE_URL: "https://www.suruga-ya.jp/product-other/109000860",
            SearchParser.CATEGORY: "ニンテンドースイッチソフト",
            SearchParser.MAKEPURE_URL: "https://www.suruga-ya.jp/product-other/109000860",
            SearchParser.MAKEPURE: "￥2,790",
            SearchParser.MAKEPURE_BIKO: "(16点の中古品)",
        },
        "surugaya2": {
            SearchParser.STORENAME: "駿河屋",
            SearchParser.IMAGE_URL: "https://www.suruga-ya.jp/database/photo.php?shinaban=109002738&amp;size=m",
            SearchParser.TITLE: "ゼルダの伝説 ティアーズ オブ ザ キングダム [通常版]",
            SearchParser.TITLE_URL: "https://www.suruga-ya.jp/product/detail/109002738",
            SearchParser.CATEGORY: "ニンテンドースイッチソフト",
            SearchParser.NEW: "新品：￥6,600税込",
            SearchParser.USED: "中古：￥5,980税込",
            SearchParser.MAKEPURE_URL: "https://www.suruga-ya.jp/product-other/109002738",
            SearchParser.MAKEPURE: "￥5,801",
            SearchParser.MAKEPURE_BIKO: "(16点の中古品と新品)",
        },
        "surugaya3": {
            SearchParser.STORENAME: "駿河屋",
            SearchParser.IMAGE_URL: "https://www.suruga-ya.jp/database/photo.php?shinaban=128079420&size=m",
            SearchParser.TITLE: "ジブリがいっぱい 監督もいっぱい コレクション",
            SearchParser.TITLE_URL: "https://www.suruga-ya.jp/product/detail/128079420?tenpo_cd=",
            SearchParser.CATEGORY: "アニメDVD",
            SearchParser.SINAGIRE: "品切れ",
        },
        "bookoff1": {
            SearchParser.STORENAME: "ブックオフ",
            SearchParser.IMAGE_URL: "https://content.bookoff.co.jp/goodsimages/LL/001046/0010467610LL.jpg",
            SearchParser.TITLE: "ハウルの動く城",
            SearchParser.TITLE_URL: "https://shopping.bookoff.co.jp/used/0010467610",
            SearchParser.CATEGORY: "ＤＶＤ",
            SearchParser.USED: "1,430円",
            SearchParser.IMAGE_ON_ERR: bookoff_img_on_err,
        },
        "bookoff2": {
            SearchParser.STORENAME: "ネットオフ",
            SearchParser.IMAGE_URL: "https://www.netoff.co.jp/ebimage/cmdty/0013442958.jpg",
            SearchParser.TITLE: "【特典ディスク付】耳をすませば",
            SearchParser.TITLE_URL: "https://www.netoff.co.jp/detail/0013442958",
            SearchParser.CATEGORY: "DVD",
            SearchParser.USED: "価格：￥3,298円",
            SearchParser.SINAGIRE: "品切れ",
            SearchParser.IMAGE_ON_ERR: netoff_img_on_err,
        },
    }
    sris: list[SearchResultItem] = SearchDictConverter.convertToSearchResultItems(
        list(items_dict.values())
    )
    for i, key in zip(sris, items_dict.keys()):
        if key == "surugaya1":
            __item_common_assert(i, items_dict, key)
            __item_makepure_assert(i, items_dict, key)
        if key == "surugaya2":
            __item_common_assert(i, items_dict, key)
            assert i.main != None
            assert i.main.new != None
            assert i.main.new.price == items_dict[key][SearchParser.NEW][3:9]
            assert i.main.new.price_pre_text == items_dict[key][SearchParser.NEW][:3]
            assert i.main.new.price_tail_text == items_dict[key][SearchParser.NEW][9:]
            __item_makepure_assert(i, items_dict, key)
            assert i.main.used != None
            assert i.main.used.price == items_dict[key][SearchParser.USED][3:9]
            assert i.main.used.price_pre_text == items_dict[key][SearchParser.USED][:3]
            assert i.main.used.price_tail_text == items_dict[key][SearchParser.USED][9:]
        if key == "surugaya3":
            __item_common_assert(i, items_dict, key)
            assert i.sinagire == items_dict[key][SearchParser.SINAGIRE]
            assert i.main != None
            assert i.main.new is None
            assert i.main.used is None
        if key == "bookoff1":
            __item_common_assert(i, items_dict, key)
            assert i.main.used != None
            assert i.main.used.price == items_dict[key][SearchParser.USED]
            assert i.img_on_err == items_dict[key][SearchParser.IMAGE_ON_ERR]
        if key == "bookoff2":
            __item_common_assert(i, items_dict, key)
            assert i.sinagire == items_dict[key][SearchParser.SINAGIRE]
            assert i.main.used != None
            assert i.main.used.price == ""
            assert i.main.used.price_pre_text == ""
            assert i.main.used.price_tail_text == ""
            assert i.img_on_err == items_dict[key][SearchParser.IMAGE_ON_ERR]


def __item_common_assert(i: SearchResultItem, items, key: str):
    assert i.storename == items[key][SearchParser.STORENAME]
    assert i.img == items[key][SearchParser.IMAGE_URL]
    assert i.title == items[key][SearchParser.TITLE]
    assert i.item_url == items[key][SearchParser.TITLE_URL]
    assert i.category == items[key][SearchParser.CATEGORY]


def __item_makepure_assert(i: SearchResultItem, items, key: str):
    assert i.makepure != None
    assert i.makepure.price == items[key][SearchParser.MAKEPURE]
    assert i.makepure.biko == items[key][SearchParser.MAKEPURE_BIKO]
    assert i.makepure.url == items[key][SearchParser.MAKEPURE_URL]


def test_convertToSearchResultPage_full():
    pageinfo = {
        SearchCmn.ENABLE: SearchCmn.TRUE,
        SearchCmn.MAX: 5,
        SearchCmn.MIN: 1,
        SearchCmn.MOREPAGE: SearchCmn.TRUE,
        SearchCmn.CURRENT: 2,
    }
    urlparam = {
        FilterQueryName.WORD.value: "ジブリ",
        FilterQueryName.STORE.value: [1],
        SearchParser.CATEGORY: 1,
        "safesaerch": 0,
        SearchParser.ZAIKO: 1,
    }
    srp: SearchResultPage = SearchDictConverter.convertToSearchResultPage(
        pageinfo, urlparam
    )

    next_url = SearchDictConverter.createURLParam(
        urlparam, pageinfo[SearchCmn.CURRENT] + 1
    )
    pre_url = SearchDictConverter.createURLParam(
        urlparam, pageinfo[SearchCmn.CURRENT] - 1
    )
    assert srp.next_url == next_url
    assert srp.pre_url == pre_url
    assert srp.more_page == True
    assert not srp.pages is None
    for page in srp.pages:
        if page.cure_page:
            assert page.num == pageinfo[SearchCmn.CURRENT]
        assert page.url == SearchDictConverter.createURLParam(urlparam, page.num)


def test_convertToSearchResultPage_first_page():
    pageinfo = {
        SearchCmn.ENABLE: SearchCmn.TRUE,
        SearchCmn.MAX: 3,
        SearchCmn.MIN: 1,
        SearchCmn.MOREPAGE: SearchCmn.FALSE,
        SearchCmn.CURRENT: 1,
    }
    urlparam = {
        FilterQueryName.WORD.value: "ジブリ",
        FilterQueryName.STORE.value: [1, 2],
        SearchParser.CATEGORY: 1,
    }
    srp: SearchResultPage = SearchDictConverter.convertToSearchResultPage(
        pageinfo, urlparam
    )

    assert srp.next_url == SearchDictConverter.createURLParam(
        urlparam, pageinfo[SearchCmn.CURRENT] + 1
    )
    assert srp.pre_url == None
    assert srp.more_page == False
    assert not srp.pages is None
    for page in srp.pages:
        if page.cure_page:
            assert page.num == pageinfo[SearchCmn.CURRENT]
        assert page.url == SearchDictConverter.createURLParam(urlparam, page.num)


def test_convertToSearchResultPage_first_page_only():
    pageinfo = {
        SearchCmn.ENABLE: SearchCmn.TRUE,
        SearchCmn.MAX: 1,
        SearchCmn.MIN: 1,
        SearchCmn.MOREPAGE: SearchCmn.FALSE,
        SearchCmn.CURRENT: 1,
    }
    urlparam = {
        FilterQueryName.WORD.value: "ジブリ",
        FilterQueryName.STORE.value: [1, 2],
        SearchParser.CATEGORY: 7,
        "safesaerch": 1,
        SearchParser.ZAIKO: 0,
    }
    srp: SearchResultPage = SearchDictConverter.convertToSearchResultPage(
        pageinfo, urlparam
    )

    assert srp.next_url == None
    assert srp.pre_url == None
    assert srp.more_page == False
    assert not srp.pages is None
    for page in srp.pages:
        if page.cure_page:
            assert page.num == pageinfo[SearchCmn.CURRENT]
        assert page.url == SearchDictConverter.createURLParam(urlparam, page.num)


def test_convertToSearchResultPage_max_page():
    pageinfo = {
        SearchCmn.ENABLE: SearchCmn.TRUE,
        SearchCmn.MAX: 3,
        SearchCmn.MIN: 1,
        SearchCmn.MOREPAGE: SearchCmn.FALSE,
        SearchCmn.CURRENT: 3,
    }
    urlparam = {
        FilterQueryName.WORD.value: "ジブリ",
        FilterQueryName.STORE.value: [3, 2],
        SearchParser.CATEGORY: 2,
    }
    srp: SearchResultPage = SearchDictConverter.convertToSearchResultPage(
        pageinfo, urlparam
    )

    assert srp.next_url == None
    assert srp.pre_url == SearchDictConverter.createURLParam(
        urlparam, pageinfo[SearchCmn.CURRENT] - 1
    )
    assert srp.more_page == False
    assert not srp.pages is None
    for page in srp.pages:
        if page.cure_page:
            assert page.num == pageinfo[SearchCmn.CURRENT]
        assert page.url == SearchDictConverter.createURLParam(urlparam, page.num)


def test_convertToSearchResultPage_many_page():
    pageinfo = {
        SearchCmn.ENABLE: SearchCmn.TRUE,
        SearchCmn.MAX: 11,
        SearchCmn.MIN: 7,
        SearchCmn.MOREPAGE: SearchCmn.TRUE,
        SearchCmn.CURRENT: 10,
    }
    urlparam = {
        FilterQueryName.WORD.value: "ジブリ",
        FilterQueryName.STORE.value: [4],
        SearchParser.CATEGORY: 10,
    }
    srp: SearchResultPage = SearchDictConverter.convertToSearchResultPage(
        pageinfo, urlparam
    )

    assert srp.next_url == SearchDictConverter.createURLParam(
        urlparam, pageinfo[SearchCmn.CURRENT] + 1
    )
    assert srp.pre_url == SearchDictConverter.createURLParam(
        urlparam, pageinfo[SearchCmn.CURRENT] - 1
    )
    assert srp.more_page == True
    assert not srp.pages is None
    for page in srp.pages:
        if page.cure_page:
            assert page.num == pageinfo[SearchCmn.CURRENT]
        assert page.url == SearchDictConverter.createURLParam(urlparam, page.num)


def test_convertMainItem_for_new():
    SURUGAYA = "駿河屋"
    item_dict = {
        SURUGAYA: {
            SearchParser.STORENAME: "駿河屋",
            SearchParser.IMAGE_URL: "https://www.suruga-ya.jp/database/photo.php?shinaban=109002738&amp;size=m",
            SearchParser.TITLE: "ゼルダの伝説 ティアーズ オブ ザ キングダム [通常版]",
            SearchParser.TITLE_URL: "https://www.suruga-ya.jp/product/detail/109002738",
            SearchParser.CATEGORY: "ニンテンドースイッチソフト",
            SearchParser.NEW: "新品：￥6,600税込",
            SearchParser.MAKEPURE_URL: "https://www.suruga-ya.jp/product-other/109002738",
            SearchParser.MAKEPURE: "￥5,801",
            SearchParser.MAKEPURE_BIKO: "(16点の中古品と新品)",
        },
    }
    results = {}
    results[SURUGAYA] = SearchDictConverter.convertMainItem(item_dict[SURUGAYA])
    __check_new(
        results[SURUGAYA],
        item_dict[SURUGAYA][SearchParser.TITLE],
        item_dict[SURUGAYA][SearchParser.TITLE_URL],
        item_dict[SURUGAYA][SearchParser.NEW][3:9],
        item_dict[SURUGAYA][SearchParser.NEW][:3],
        item_dict[SURUGAYA][SearchParser.NEW][9:],
    )


def __check_new(
    main: MainItem,
    title: str,
    title_url: str,
    price: str,
    pre_text: str,
    tail_text: str,
):
    assert main != None
    assert main.title == title
    assert main.url == title_url
    assert main.new != None
    assert main.new.price == price
    assert main.new.price_pre_text == pre_text
    assert main.new.price_tail_text == tail_text


def test_convertMainItem_for_range():
    SURUGAYA = "駿河屋"
    item_dict = {
        SURUGAYA: {
            SearchParser.STORENAME: "駿河屋",
            SearchParser.IMAGE_URL: "https://www.suruga-ya.jp/database/photo.php?shinaban=109102234&size=m",
            SearchParser.TITLE: "マリオカート ライブ ホームサーキット マリオセット",
            SearchParser.TITLE_URL: "https://www.suruga-ya.jp/product/detail/109102234",
            SearchParser.CATEGORY: "ニンテンドースイッチハード",
            SearchParser.USED: "中古：￥3,440～￥4,300税込",
            SearchParser.MAKEPURE_URL: "https://www.suruga-ya.jp/product/other/109102234",
            SearchParser.MAKEPURE: "￥3,040",
            SearchParser.MAKEPURE_BIKO: "(11点の中古品)",
        },
    }
    results = {}
    results[SURUGAYA] = SearchDictConverter.convertMainItem(item_dict[SURUGAYA])
    __check_used(
        results[SURUGAYA],
        item_dict[SURUGAYA][SearchParser.TITLE],
        item_dict[SURUGAYA][SearchParser.TITLE_URL],
        item_dict[SURUGAYA][SearchParser.USED][3:16],
        item_dict[SURUGAYA][SearchParser.USED][:3],
        item_dict[SURUGAYA][SearchParser.USED][16:],
    )


def __check_used(
    main: MainItem,
    title: str,
    title_url: str,
    price: str,
    pre_text: str,
    tail_text: str,
):
    assert main != None
    assert main.title == title
    assert main.url == title_url
    assert main.used != None
    assert main.used.price == price
    assert main.used.price_pre_text == pre_text
    assert main.used.price_tail_text == tail_text

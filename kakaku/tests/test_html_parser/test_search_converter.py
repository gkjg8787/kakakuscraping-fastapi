from html_parser.search_converter import (
    SearchDictConverter,
    SearchResultItem,
    SearchResultPage,
    MainItem,
)
from html_parser.search_parser import SearchParser, SearchCmn
from common.filter_name import FilterQueryName

geo_img_on_err = "https://ec.geo-online.co.jp/img/sys/sorryL.jpg"
netoff_img_on_err = "https://st.netoff.co.jp/ebimage/noimage_comic_01.gif"
bookoff_img_on_err = "https://content.bookoffonline.co.jp/images/goods/item_l.gif"


def test_convertToSearchResultItems_full():
    items = [
        {
            SearchParser.STORENAME: "駿河屋",
            SearchParser.IMAGE_URL: "https://www.suruga-ya.jp/database/photo.php?shinaban=109000860&size=m",
            SearchParser.TITLE: "ポケモン不思議のダンジョン 救助隊DX",
            SearchParser.TITLE_URL: "https://www.suruga-ya.jp/product-other/109000860",
            SearchParser.CATEGORY: "ニンテンドースイッチソフト",
            SearchParser.MAKEPURE_URL: "https://www.suruga-ya.jp/product-other/109000860",
            SearchParser.MAKEPURE: "マケプレ￥2,790",
            SearchParser.MAKEPURE_BIKO: "(16点の中古品)",
        },
        {
            SearchParser.STORENAME: "駿河屋",
            SearchParser.IMAGE_URL: "https://www.suruga-ya.jp/database/photo.php?shinaban=109002738&amp;size=m",
            SearchParser.TITLE: "ゼルダの伝説 ティアーズ オブ ザ キングダム [通常版]",
            SearchParser.TITLE_URL: "https://www.suruga-ya.jp/product/detail/109002738",
            SearchParser.CATEGORY: "ニンテンドースイッチソフト",
            SearchParser.NEW: "新品：￥6,600税込",
            SearchParser.USED: "中古：￥5,980税込",
            SearchParser.MAKEPURE_URL: "https://www.suruga-ya.jp/product-other/109002738",
            SearchParser.MAKEPURE: "マケプレ￥5,801",
            SearchParser.MAKEPURE_BIKO: "(16点の中古品と新品)",
        },
        {
            SearchParser.STORENAME: "駿河屋",
            SearchParser.IMAGE_URL: "https://www.suruga-ya.jp/database/photo.php?shinaban=128079420&size=m",
            SearchParser.TITLE: "ジブリがいっぱい 監督もいっぱい コレクション",
            SearchParser.TITLE_URL: "https://www.suruga-ya.jp/product/detail/128079420?tenpo_cd=",
            SearchParser.CATEGORY: "アニメDVD",
            SearchParser.SINAGIRE: "品切れ",
        },
        {
            SearchParser.STORENAME: "ゲオ",
            SearchParser.IMAGE_URL: "https://eccdn.geo-online.co.jp/ec_media_images/5151459-01.jpg",
            SearchParser.TITLE: "【新品】ゼルダの伝説 ティアーズ オブ ザ キングダム",
            SearchParser.TITLE_URL: "https://ec.geo-online.co.jp/shop/g/g515145901/",
            SearchParser.CATEGORY: "Nintendo Switch",
            SearchParser.STATE: "新品",
            SearchParser.NEW: "7,120円",
            SearchParser.IMAGE_ON_ERR: geo_img_on_err,
        },
        {
            SearchParser.STORENAME: "ゲオ",
            SearchParser.IMAGE_URL: "https://ec.geo-online.co.jp/img/sys/sorryL.jpg",
            SearchParser.TITLE: "【中古】ゲド戦記 【DVD】／岡田准一",
            SearchParser.TITLE_URL: "https://ec.geo-online.co.jp/shop/g/g586234102/",
            SearchParser.CATEGORY: "DVD",
            SearchParser.STATE: "状態A",
            SearchParser.USED: "2,445円",
            SearchParser.IMAGE_ON_ERR: geo_img_on_err,
        },
        {
            SearchParser.STORENAME: "ブックオフ",
            SearchParser.IMAGE_URL: "https://content.bookoff.co.jp/goodsimages/LL/001046/0010467610LL.jpg",
            SearchParser.TITLE: "ハウルの動く城",
            SearchParser.TITLE_URL: "https://shopping.bookoff.co.jp/used/0010467610",
            SearchParser.CATEGORY: "ＤＶＤ",
            SearchParser.USED: "1,430円",
            SearchParser.IMAGE_ON_ERR: bookoff_img_on_err,
        },
        {
            SearchParser.STORENAME: "ネットオフ",
            SearchParser.IMAGE_URL: "https://www.netoff.co.jp/ebimage/cmdty/0013442958.jpg",
            SearchParser.TITLE: "【特典ディスク付】耳をすませば",
            SearchParser.TITLE_URL: "https://www.netoff.co.jp/detail/0013442958",
            SearchParser.CATEGORY: "DVD",
            SearchParser.USED: "価格：￥3,298円",
            SearchParser.SINAGIRE: "品切れ",
            SearchParser.IMAGE_ON_ERR: netoff_img_on_err,
        },
    ]
    sris: list[SearchResultItem] = SearchDictConverter.convertToSearchResultItems(items)
    for num, i in enumerate(sris):
        if num == 0:
            __item_common_assert(i, items, num)
            __item_makepure_assert(i, items, num)
        if num == 1:
            __item_common_assert(i, items, num)
            assert i.main != None
            assert i.main.new != None
            assert i.main.new.price == items[num][SearchParser.NEW][3:9]
            assert i.main.new.price_pre_text == items[num][SearchParser.NEW][:3]
            assert i.main.new.price_tail_text == items[num][SearchParser.NEW][9:]
            __item_makepure_assert(i, items, num)
            assert i.main.used != None
            assert i.main.used.price == items[num][SearchParser.USED][3:9]
            assert i.main.used.price_pre_text == items[num][SearchParser.USED][:3]
            assert i.main.used.price_tail_text == items[num][SearchParser.USED][9:]
        if num == 2:
            __item_common_assert(i, items, num)
            assert i.sinagire == items[num][SearchParser.SINAGIRE]
            assert i.main != None
            assert i.main.new is None
            assert i.main.used is None
        if num == 3:
            __item_common_assert(i, items, num)
            assert i.state == items[num][SearchParser.STATE]
            assert i.main.new != None
            assert i.main.new.price == items[num][SearchParser.NEW]
            assert i.main.new.price_pre_text == ""
            assert i.main.new.price_tail_text == ""
            assert i.img_on_err == items[num][SearchParser.IMAGE_ON_ERR]
        if num == 4:
            __item_common_assert(i, items, num)
            assert i.state == items[num][SearchParser.STATE]
            assert i.main.used != None
            assert i.main.used.price == items[num][SearchParser.USED]
            assert i.main.used.price_pre_text == ""
            assert i.main.used.price_tail_text == ""
            assert i.img_on_err == items[num][SearchParser.IMAGE_ON_ERR]
        if num == 5:
            __item_common_assert(i, items, num)
            assert i.main.used != None
            assert i.main.used.price == items[num][SearchParser.USED]
            assert i.img_on_err == items[num][SearchParser.IMAGE_ON_ERR]
        if num == 6:
            __item_common_assert(i, items, num)
            assert i.sinagire == items[num][SearchParser.SINAGIRE]
            assert i.main.used != None
            assert i.main.used.price == ""  # items[num][SearchParser.USED][3:9]
            assert i.main.used.price_pre_text == ""
            assert i.main.used.price_tail_text == ""
            assert i.img_on_err == items[num][SearchParser.IMAGE_ON_ERR]


def __item_common_assert(i: SearchResultItem, items, num: int):
    assert i.storename == items[num][SearchParser.STORENAME]
    assert i.img == items[num][SearchParser.IMAGE_URL]
    assert i.title == items[num][SearchParser.TITLE]
    assert i.item_url == items[num][SearchParser.TITLE_URL]
    assert i.category == items[num][SearchParser.CATEGORY]


def __item_makepure_assert(i: SearchResultItem, items, num: int):
    assert i.makepure != None
    assert i.makepure.price == items[num][SearchParser.MAKEPURE][4:]
    assert i.makepure.biko == items[num][SearchParser.MAKEPURE_BIKO]
    assert i.makepure.url == items[num][SearchParser.MAKEPURE_URL]


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
    GEO = "ゲオ"
    item_dict = {
        SURUGAYA: {
            SearchParser.STORENAME: "駿河屋",
            SearchParser.IMAGE_URL: "https://www.suruga-ya.jp/database/photo.php?shinaban=109002738&amp;size=m",
            SearchParser.TITLE: "ゼルダの伝説 ティアーズ オブ ザ キングダム [通常版]",
            SearchParser.TITLE_URL: "https://www.suruga-ya.jp/product/detail/109002738",
            SearchParser.CATEGORY: "ニンテンドースイッチソフト",
            SearchParser.NEW: "新品：￥6,600税込",
            SearchParser.MAKEPURE_URL: "https://www.suruga-ya.jp/product-other/109002738",
            SearchParser.MAKEPURE: "マケプレ￥5,801",
            SearchParser.MAKEPURE_BIKO: "(16点の中古品と新品)",
        },
        GEO: {
            SearchParser.STORENAME: "ゲオ",
            SearchParser.IMAGE_URL: "https://eccdn.geo-online.co.jp/ec_media_images/5151459-01.jpg",
            SearchParser.TITLE: "【新品】ゼルダの伝説 ティアーズ オブ ザ キングダム",
            SearchParser.TITLE_URL: "https://ec.geo-online.co.jp/shop/g/g515145901/",
            SearchParser.CATEGORY: "Nintendo Switch",
            SearchParser.STATE: "新品",
            SearchParser.NEW: "7,120円",
            SearchParser.IMAGE_ON_ERR: geo_img_on_err,
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
    results[GEO] = SearchDictConverter.convertMainItem(item_dict[GEO])
    __check_new(
        results[GEO],
        item_dict[GEO][SearchParser.TITLE],
        item_dict[GEO][SearchParser.TITLE_URL],
        item_dict[GEO][SearchParser.NEW],
        "",
        "",
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

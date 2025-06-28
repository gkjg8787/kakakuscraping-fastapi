from datetime import datetime, timezone
from html_parser import surugaya_html_parse
from common import read_config

from .read_data import read_tgz

other_fpath = "surugaya_other.html"
shiharai_fpath = "shiharai.html"
other_url = "https://www.suruga-ya.jp/product/other/128002938"
redirect_detail_fpath = "surugaya_detail_redirect.html"
detail_timesale_fpath = "surugaya_detail_timesale.html"
other_timesale_fpath = "surugaya_other_timesale.html"
detail_other_b_rank_fpath = "surugaya_detail_other_b_rank.html"
detail_new_used_fpath = "surugaya_detail_new_used.html"


def test_surugaya_makepure_postage_storepostage():
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": False},
        "excluded_condition_keywords": [],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(other_fpath)
    sp = surugaya_html_parse.SurugayaParse(
        fp, 1, "2025-06-21 00:00:01", other_url, ipopts
    )
    assert sp.hasPostage()
    sppl = sp.getPostageList()
    for spp in sppl:
        if spp.storename == "駿河屋日本橋本館":
            assert len(spp.target_prefectures) == 0
            assert (
                spp.campaign_msg
                == "2,000円以上のお買い上げにて送料無料キャンペーン 2025/06/20 00:00 ～ 2025/06/22 23:59 2,000円未満 300～1,500円 2,000円以上 送料無料"
            )
            assert len(spp.terms) == 1
            assert spp.terms[0].boundary == "2000<="
            assert spp.terms[0].postage == 0

        if spp.storename == "駿河屋松本店":
            assert len(spp.target_prefectures) == 0
            assert len(spp.campaign_msg) == 0
            assert len(spp.terms) == 0

        if spp.storename == "りあらいず":
            assert len(spp.target_prefectures) == 0
            assert (
                spp.campaign_msg
                == "送料キャンペーン 2025/06/01 00:00 ～ 2025/06/30 23:59 100円未満 700円 10,000円未満 400円 10,000円以上 送料無料"
            )
            assert len(spp.terms) == 3
            assert spp.terms[0].boundary == "100>"
            assert spp.terms[0].postage == 700
            assert spp.terms[1].boundary == "100<=:10000>"
            assert spp.terms[1].postage == 400
            assert spp.terms[2].boundary == "10000<="
            assert spp.terms[2].postage == 0

        if spp.storename == "駿河屋":
            assert len(spp.target_prefectures) == 0
            assert (
                spp.campaign_msg
                == "6/21 ～ 6/22【999円以上】代引き100円+送料無料 2025/06/21 00:00 ～ 2025/06/22 23:59 999円未満 440円 999円以上 送料無料"
            )
            assert len(spp.terms) == 2
            assert spp.terms[0].boundary == "999>"
            assert spp.terms[0].postage == 440
            assert spp.terms[1].boundary == "999<="
            assert spp.terms[1].postage == 0


def test_surugaya_makepure_postage_shopidinfo():
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": False},
        "excluded_condition_keywords": [],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(other_fpath)
    sp = surugaya_html_parse.SurugayaParse(
        fp, 1, "2025-06-21 00:00:01", other_url, ipopts
    )
    assert sp.hasShopIDInfo()
    sidinf = sp.getShopIDInfo()
    base_url = "https://www.suruga-ya.jp/shop/"
    for key, val in sidinf.items():
        if key == "駿河屋日本橋本館":
            assert val.storename == key
            assert val.shop_id == 200823
            assert val.url == base_url + "200823"
        if key == "駿河屋 ひたちなかファッションクルーズ店":
            assert val.storename == key
            assert val.shop_id == 400515
            assert val.url == base_url + "400515"
        if key == "ブックマーケット利府店 Supported by 駿河屋":
            assert val.storename == key
            assert val.shop_id == 201267
            assert val.url == base_url + "201267"
        if key == "りあらいず":
            assert val.storename == key
            assert val.shop_id == 400389
            assert val.url == base_url + "400389"


def test_surugaya_shiharai_parse():
    fp = read_tgz(shiharai_fpath)
    sp = surugaya_html_parse.SurugayaShiharaiParse(fp)
    for psp in sp.get_ParseStorePostage():
        assert psp.storename == "駿河屋"
        if "東京" in psp.target_prefectures:
            assert len(psp.target_prefectures) == 34 + 7 + 4
            assert len(psp.terms) == 2
            assert psp.terms[0].boundary == "5000>"
            assert psp.terms[0].postage == 240
            assert psp.terms[1].boundary == "5000<="
            assert psp.terms[1].postage == 0
            continue
        if "北海道" in psp.target_prefectures:
            assert len(psp.target_prefectures) == 2
            assert len(psp.terms) == 3
            assert psp.terms[0].boundary == "5000>"
            assert psp.terms[0].postage == 570
            assert psp.terms[1].boundary == "5000<=:10000>"
            assert psp.terms[1].postage == 285
            assert psp.terms[2].boundary == "10000<="
            assert psp.terms[2].postage == 0
            continue


def test_surugaya_detail_redirect():
    correct = {
        "url_id": 1,
        "uniqname": "WiiUソフトマリオパーティ10 amiiboセット(状態：外箱欠品)",
        "usedprice": 3209,
        "newprice": -1,
        "taxin": True,
        "onsale": False,
        "salename": "",
        "issuccess": True,
        "oldprice": -1,
        "trendrate": 0,
        "url": "https://www.suruga-ya.jp/product/detail/106000370?tenpo_cd=400438",
        "storename": "バリQ古河ホビー館 Supported by 駿河屋",
        "created_at": datetime(2024, 10, 28, 10, 30, tzinfo=timezone.utc),
    }
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": False},
        "excluded_condition_keywords": [],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(redirect_detail_fpath)
    sp = surugaya_html_parse.SurugayaParse(
        fp=fp,
        id=correct["url_id"],
        date=correct["created_at"],
        url=correct["url"],
        itemparseoptions=ipopts,
    )
    for item in sp.getItems():
        for key, val in item.getOrderedDict().items():
            assert val == correct[key]

    assert sp.hasPostage()
    assert len(sp.getPostageList()) == 1
    for pos in sp.getPostageList():
        assert pos.storename == correct["storename"]
        assert pos.campaign_msg == ""
        assert len(pos.target_prefectures) == 0
        assert len(pos.terms) == 0

    assert sp.hasShopIDInfo()
    assert sp.getShopIDInfo()[correct["storename"]].storename == correct["storename"]
    assert sp.getShopIDInfo()[correct["storename"]].shop_id == 400438
    assert (
        sp.getShopIDInfo()[correct["storename"]].url
        == "https://www.suruga-ya.jp/shop/400438"
    )


def test_surugaya_detail_timesale():
    correct = {
        "url_id": 1,
        "uniqname": "アニメDVDもののけ姫",
        "usedprice": 2800,
        "newprice": -1,
        "taxin": True,
        "onsale": True,
        "salename": "タイムセール",
        "issuccess": True,
        "oldprice": -1,
        "trendrate": 0,
        "url": "https://www.suruga-ya.jp/product/detail/128049960",
        "storename": "駿河屋",
        "created_at": datetime(2024, 12, 6, 20, 3, tzinfo=timezone.utc),
    }
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": False},
        "excluded_condition_keywords": [],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(detail_timesale_fpath)
    sp = surugaya_html_parse.SurugayaParse(
        fp=fp,
        id=correct["url_id"],
        date=correct["created_at"],
        url=correct["url"],
        itemparseoptions=ipopts,
    )
    for item in sp.getItems():
        for key, val in item.getOrderedDict().items():
            assert val == correct[key]

    assert not sp.hasPostage()


def test_surugaya_other_timesale():
    corrects = [
        {
            "url_id": 1,
            "uniqname": "もののけ姫",
            "usedprice": 2800,
            "newprice": -1,
            "taxin": True,
            "onsale": True,
            "salename": "タイムセール",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/other/128049960",
            "storename": "駿河屋",
            "created_at": datetime(2024, 12, 6, 20, 3, tzinfo=timezone.utc),
            "campaign_msg": "12/6 ～ 12/7【999円以上】代引き+送料無料 2024/12/06 00:00 ～ 2024/12/07 23:59 999円未満 440円 999円以上 送料無料",
            "target_prefectures_length": 0,
            "terms_length": 2,
        },
        {
            "url_id": 1,
            "uniqname": "もののけ姫",
            "usedprice": 2950,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/other/128049960",
            "storename": "駿河屋 佐大通り店",
            "created_at": datetime(2024, 12, 6, 20, 3, tzinfo=timezone.utc),
            "campaign_msg": "",
            "target_prefectures_length": 0,
            "terms_length": 0,
        },
    ]
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": False},
        "excluded_condition_keywords": [],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(other_timesale_fpath)
    sp = surugaya_html_parse.SurugayaParse(
        fp=fp,
        id=corrects[0]["url_id"],
        date=corrects[0]["created_at"],
        url=corrects[0]["url"],
        itemparseoptions=ipopts,
    )
    for item, correct in zip(sp.getItems(), corrects):
        for key, val in item.getOrderedDict().items():
            assert val == correct[key]

    assert sp.hasPostage()

    assert len(sp.getPostageList()) == 2
    for pos, correct in zip(sp.getPostageList(), corrects):
        assert pos.storename == correct["storename"]
        assert pos.campaign_msg == correct["campaign_msg"]
        assert len(pos.target_prefectures) == correct["target_prefectures_length"]
        assert len(pos.terms) == correct["terms_length"]

    assert sp.hasShopIDInfo()
    assert (
        sp.getShopIDInfo()[corrects[1]["storename"]].storename
        == corrects[1]["storename"]
    )
    assert sp.getShopIDInfo()[corrects[1]["storename"]].shop_id == 400506
    assert (
        sp.getShopIDInfo()[corrects[1]["storename"]].url
        == "https://www.suruga-ya.jp/shop/400506"
    )


def test_surugaya_detail_other_items():
    corrects = [
        {
            "url_id": 1,
            "uniqname": "ニンテンドースイッチハードマリオカート ライブ ホームサーキット マリオセット",
            "usedprice": 4680,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/detail/109102234",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "ニンテンドースイッチハードマリオカート ライブ ホームサーキット マリオセット",
            "usedprice": 3740,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/detail/109102234",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "ニンテンドースイッチハードマリオカート ライブ ホームサーキット マリオセット",
            "usedprice": 3450,
            "newprice": -1,
            "taxin": True,
            "onsale": True,
            "salename": "タイムセール",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/detail/109102234",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "ニンテンドースイッチハードマリオカート ライブ ホームサーキット マリオセット",
            "usedprice": 3060,
            "newprice": -1,
            "taxin": True,
            "onsale": True,
            "salename": "タイムセール",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/detail/109102234",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
    ]
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": True},
        "excluded_condition_keywords": [],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(detail_other_b_rank_fpath)
    sp = surugaya_html_parse.SurugayaParse(
        fp=fp,
        id=corrects[0]["url_id"],
        date=corrects[0]["created_at"],
        url=corrects[0]["url"],
        itemparseoptions=ipopts,
    )
    items = sp.getItems()
    assert len(items) == len(corrects)
    for i in range(len(items)):
        item = items[i]
        correct = corrects[i]
        for key, val in item.getOrderedDict().items():
            assert val == correct[key]

    assert not sp.hasPostage()


def test_surugaya_detail_other_items_not_other():
    corrects = [
        {
            "url_id": 1,
            "uniqname": "ニンテンドースイッチハードマリオカート ライブ ホームサーキット マリオセット",
            "usedprice": 4680,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/detail/109102234",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
    ]
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": False},
        "excluded_condition_keywords": [],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(detail_other_b_rank_fpath)
    sp = surugaya_html_parse.SurugayaParse(
        fp=fp,
        id=corrects[0]["url_id"],
        date=corrects[0]["created_at"],
        url=corrects[0]["url"],
        itemparseoptions=ipopts,
    )
    items = sp.getItems()
    assert len(items) == len(corrects)
    for i in range(len(items)):
        item = items[i]
        correct = corrects[i]
        for key, val in item.getOrderedDict().items():
            assert val == correct[key]


def test_surugaya_detail_other_items_excluded_one():
    corrects = [
        {
            "url_id": 1,
            "uniqname": "ニンテンドースイッチハードマリオカート ライブ ホームサーキット マリオセット",
            "usedprice": 4680,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/detail/109102234",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "ニンテンドースイッチハードマリオカート ライブ ホームサーキット マリオセット",
            "usedprice": 3740,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/detail/109102234",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "ニンテンドースイッチハードマリオカート ライブ ホームサーキット マリオセット",
            "usedprice": 3450,
            "newprice": -1,
            "taxin": True,
            "onsale": True,
            "salename": "タイムセール",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/detail/109102234",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
    ]
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": True},
        "excluded_condition_keywords": ["難"],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(detail_other_b_rank_fpath)
    sp = surugaya_html_parse.SurugayaParse(
        fp=fp,
        id=corrects[0]["url_id"],
        date=corrects[0]["created_at"],
        url=corrects[0]["url"],
        itemparseoptions=ipopts,
    )
    items = sp.getItems()
    assert len(items) == len(corrects)
    for i in range(len(items)):
        item = items[i]
        correct = corrects[i]
        for key, val in item.getOrderedDict().items():
            assert val == correct[key]


def test_surugaya_detail_other_items_excluded_two():
    corrects = [
        {
            "url_id": 1,
            "uniqname": "ニンテンドースイッチハードマリオカート ライブ ホームサーキット マリオセット",
            "usedprice": 4680,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/detail/109102234",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "ニンテンドースイッチハードマリオカート ライブ ホームサーキット マリオセット",
            "usedprice": 3740,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/detail/109102234",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
    ]
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": True},
        "excluded_condition_keywords": ["欠品"],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(detail_other_b_rank_fpath)
    sp = surugaya_html_parse.SurugayaParse(
        fp=fp,
        id=corrects[0]["url_id"],
        date=corrects[0]["created_at"],
        url=corrects[0]["url"],
        itemparseoptions=ipopts,
    )
    items = sp.getItems()
    assert len(items) == len(corrects)
    for i in range(len(items)):
        item = items[i]
        correct = corrects[i]
        for key, val in item.getOrderedDict().items():
            assert val == correct[key]


def test_surugaya_other_excluded_condition():
    corrects = [
        {
            "url_id": 1,
            "uniqname": "となりのトトロ",
            "usedprice": 2440,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/other/128002938",
            "storename": "駿河屋 ひたちなかファッションクルーズ店",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "となりのトトロ",
            "usedprice": 3180,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/other/128002938",
            "storename": "駿河屋神戸兵庫駅前店",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "となりのトトロ",
            "usedprice": 3200,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/other/128002938",
            "storename": "駿河屋日本橋本館",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "となりのトトロ",
            "usedprice": 3580,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/other/128002938",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "となりのトトロ",
            "usedprice": 4500,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/other/128002938",
            "storename": "駿河屋藤枝店",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
    ]
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": False},
        "excluded_condition_keywords": ["不備"],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(other_fpath)
    sp = surugaya_html_parse.SurugayaParse(
        fp=fp,
        id=corrects[0]["url_id"],
        date=corrects[0]["created_at"],
        url=corrects[0]["url"],
        itemparseoptions=ipopts,
    )
    items = sp.getItems()
    assert len(items) == 10

    def assert_target_item(item, correct):
        for key, val in item.getOrderedDict().items():
            assert val == correct[key]

    assert_target_item(items[0], corrects[0])
    assert_target_item(items[1], corrects[1])
    assert_target_item(items[2], corrects[2])
    assert_target_item(items[-2], corrects[3])
    assert_target_item(items[-1], corrects[4])


def test_surugaya_detail_new_used_items():
    corrects = [
        {
            "url_id": 1,
            "uniqname": "ニンテンドースイッチ2ソフトマリオカート ワールド",
            "usedprice": -1,
            "newprice": 8483,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/detail/112000010",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 28, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "ニンテンドースイッチ2ソフトマリオカート ワールド",
            "usedprice": 7860,
            "newprice": -1,
            "taxin": True,
            "onsale": True,
            "salename": "タイムセール",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/detail/112000010",
            "storename": "駿河屋",
            "created_at": datetime(2025, 6, 28, 14, 17, tzinfo=timezone.utc),
        },
    ]
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": False},
        "excluded_condition_keywords": [],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(detail_new_used_fpath)
    sp = surugaya_html_parse.SurugayaParse(
        fp=fp,
        id=corrects[0]["url_id"],
        date=corrects[0]["created_at"],
        url=corrects[0]["url"],
        itemparseoptions=ipopts,
    )
    items = sp.getItems()
    assert len(items) == len(corrects)
    for i in range(len(items)):
        item = items[i]
        correct = corrects[i]
        for key, val in item.getOrderedDict().items():
            assert val == correct[key]

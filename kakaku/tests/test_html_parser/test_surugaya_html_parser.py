import re
from bs4 import BeautifulSoup
from pytest_httpx import HTTPXMock
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


def setup_surugaya_httpx_mock(httpx_mock: HTTPXMock, fp: str):
    # 外部通信のレスポンスとなる送料キャンペーンHTMLを生成
    shipping_html = """
    <li class="padT5 lineH20">
        <div>3,000円以上お買い上げで送料無料キャンペーン</div>
        <div class="campaign_price">
            <span class="padR5">3,000円未満</span>
            <span class="padL5">500円</span>
        </div>
        <div class="campaign_price">
            <span class="padR5">3,000円以上</span>
            <span class="padL5">送料無料</span>
        </div>
    </li>
    """
    soup = BeautifulSoup(fp, "html.parser")
    # HTML内のプレースホルダーを探して、APIレスポンスの項目を作成
    placeholders = soup.select(".ajax-campaign-placeholder")
    items = [{"id_element": p.get("id"), "html": shipping_html} for p in placeholders]

    httpx_mock.add_response(
        method="POST",
        url=re.compile(r"https://www.suruga-ya.jp/.*"),
        json={"status": "success", "items": items},
    )


def test_surugaya_makepure_postage_storepostage(httpx_mock: HTTPXMock):
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": False},
        "excluded_condition_keywords": [],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(other_fpath)
    setup_surugaya_httpx_mock(httpx_mock, fp)
    sp = surugaya_html_parse.SurugayaParse(
        fp, 1, "2025-06-21 00:00:01", other_url, ipopts
    )
    assert sp.hasPostage()
    sppl = sp.getPostageList()

    # 新しい店舗リストに対して送料パース結果を確認
    target_stores = [
        "駿河屋天文館店",
        "駿河屋 鴻巣吹上店",
        "駿河屋 盛岡MOSSビル店",
        "駿河屋 梅田茶屋町店",
        "駿河屋 市原五井店",
    ]
    for spp in sppl:
        if spp.storename in target_stores:
            assert "3,000円以上お買い上げで送料無料キャンペーン" in spp.campaign_msg
            assert len(spp.terms) == 2
            assert spp.terms[0].boundary == "3000>"
            assert spp.terms[0].postage == 500
            assert spp.terms[1].boundary == "3000<="
            assert spp.terms[1].postage == 0


def test_surugaya_makepure_postage_shopidinfo(httpx_mock: HTTPXMock):
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": False},
        "excluded_condition_keywords": [],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(other_fpath)
    setup_surugaya_httpx_mock(httpx_mock, fp)
    sp = surugaya_html_parse.SurugayaParse(
        fp, 1, "2025-06-21 00:00:01", other_url, ipopts
    )
    assert sp.hasShopIDInfo()
    sidinf = sp.getShopIDInfo()
    base_url = "https://www.suruga-ya.jp/shop/"

    shop_info = {
        # 古い情報
        "駿河屋日本橋本館": {
            "storename": "駿河屋日本橋本館",
            "shop_id": 200823,
            "url": base_url + "200823",
        },
        "駿河屋 ひたちなかファッションクルーズ店": {
            "storename": "駿河屋 ひたちなかファッションクルーズ店",
            "shop_id": 400515,
            "url": base_url + "400515",
        },
        "ブックマーケット利府店 Supported by 駿河屋": {
            "storename": "ブックマーケット利府店 Supported by 駿河屋",
            "shop_id": 201267,
            "url": base_url + "201267",
        },
        "りあらいず": {
            "storename": "りあらいず",
            "shop_id": 400389,
            "url": base_url + "400389",
        },
        # 必要な情報
        "駿河屋天文館店": {
            "storename": "駿河屋天文館店",
            "shop_id": 400496,
            "url": base_url + "400496",
        },
        "駿河屋 鴻巣吹上店": {
            "storename": "駿河屋 鴻巣吹上店",
            "shop_id": 400446,
            "url": base_url + "400446",
        },
        "駿河屋 盛岡MOSSビル店": {
            "storename": "駿河屋 盛岡MOSSビル店",
            "shop_id": 400546,
            "url": base_url + "400546",
        },
        "駿河屋 梅田茶屋町店": {
            "storename": "駿河屋 梅田茶屋町店",
            "shop_id": 400493,
            "url": base_url + "400493",
        },
        "駿河屋 市原五井店": {
            "storename": "駿河屋 市原五井店",
            "shop_id": 400507,
            "url": base_url + "400507",
        },
    }
    for key, val in sidinf.items():
        assert key in shop_info.keys()
        assert val.storename == shop_info[key]["storename"]
        assert val.shop_id == shop_info[key]["shop_id"]
        assert val.url == shop_info[key]["url"]


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


def test_surugaya_other_timesale(httpx_mock: HTTPXMock):
    corrects = [
        {
            "url_id": 1,
            "uniqname": "となりのトトロ ＆ 火垂るの墓 2本立てブルーレイ特別セット",
            "usedprice": 6000,
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
            "campaign_msg": "3,000円以上お買い上げで送料無料キャンペーン 3,000円未満 500円 3,000円以上 送料無料",
            "target_prefectures_length": 0,
            "terms_length": 2,
        },
        {
            "url_id": 1,
            "uniqname": "となりのトトロ ＆ 火垂るの墓 2本立てブルーレイ特別セット",
            "usedprice": 8300,
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
            "campaign_msg": "3,000円以上お買い上げで送料無料キャンペーン 3,000円未満 500円 3,000円以上 送料無料",
            "target_prefectures_length": 0,
            "terms_length": 2,
        },
        {
            "url_id": 1,
            "uniqname": "となりのトトロ ＆ 火垂るの墓 2本立てブルーレイ特別セット",
            "usedprice": 9220,
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
            "campaign_msg": "3,000円以上お買い上げで送料無料キャンペーン 3,000円未満 500円 3,000円以上 送料無料",
            "target_prefectures_length": 0,
            "terms_length": 2,
        },
        {
            "url_id": 1,
            "uniqname": "となりのトトロ ＆ 火垂るの墓 2本立てブルーレイ特別セット",
            "usedprice": 9511,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/other/128049960",
            "storename": "駿河屋日本橋本館",
            "created_at": datetime(2024, 12, 6, 20, 3, tzinfo=timezone.utc),
            "campaign_msg": "3,000円以上お買い上げで送料無料キャンペーン 3,000円未満 500円 3,000円以上 送料無料",
            "target_prefectures_length": 0,
            "terms_length": 2,
        },
    ]
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": False},
        "excluded_condition_keywords": [],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(other_timesale_fpath)
    setup_surugaya_httpx_mock(httpx_mock, fp)
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

    assert len(sp.getPostageList()) == 3
    for pos, correct in zip(
        sp.getPostageList(), [corrects[0], corrects[2], corrects[3]]
    ):
        assert pos.storename == correct["storename"]
        assert pos.campaign_msg == correct["campaign_msg"]
        assert len(pos.target_prefectures) == correct["target_prefectures_length"]
        assert len(pos.terms) == correct["terms_length"]

    assert sp.hasShopIDInfo()
    assert (
        sp.getShopIDInfo()[corrects[2]["storename"]].storename
        == corrects[2]["storename"]
    )
    assert sp.getShopIDInfo()[corrects[2]["storename"]].shop_id == 400506
    assert (
        sp.getShopIDInfo()[corrects[2]["storename"]].url
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


def test_surugaya_other_excluded_condition(httpx_mock: HTTPXMock):
    corrects = [
        {
            "url_id": 1,
            "uniqname": "風の谷のナウシカ [コレクターズBOX] ",
            "usedprice": 11460,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/other/128002938",
            "storename": "駿河屋 鴻巣吹上店",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "風の谷のナウシカ [コレクターズBOX] ",
            "usedprice": 14800,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/other/128002938",
            "storename": "駿河屋 盛岡MOSSビル店",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "風の谷のナウシカ [コレクターズBOX] ",
            "usedprice": 15000,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/other/128002938",
            "storename": "駿河屋 梅田茶屋町店",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
        {
            "url_id": 1,
            "uniqname": "風の谷のナウシカ [コレクターズBOX] ",
            "usedprice": 24200,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": "",
            "issuccess": True,
            "oldprice": -1,
            "trendrate": 0,
            "url": "https://www.suruga-ya.jp/product/other/128002938",
            "storename": "駿河屋 市原五井店",
            "created_at": datetime(2025, 6, 21, 14, 17, tzinfo=timezone.utc),
        },
    ]
    ipopts_dict = {
        "surugaya": {"get_other_items_in_detail_page": False},
        "excluded_condition_keywords": ["不備", "欠品"],
    }
    ipopts = read_config.ItemParseOptions(**ipopts_dict)
    fp = read_tgz(other_fpath)
    setup_surugaya_httpx_mock(httpx_mock, fp)
    sp = surugaya_html_parse.SurugayaParse(
        fp=fp,
        id=corrects[0]["url_id"],
        date=corrects[0]["created_at"],
        url=corrects[0]["url"],
        itemparseoptions=ipopts,
    )
    items = sp.getItems()
    assert len(items) == 4

    def assert_target_item(item, correct):
        for key, val in item.getOrderedDict().items():
            assert val == correct[key]

    assert_target_item(items[0], corrects[0])
    assert_target_item(items[1], corrects[1])
    assert_target_item(items[2], corrects[2])
    assert_target_item(items[3], corrects[3])


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

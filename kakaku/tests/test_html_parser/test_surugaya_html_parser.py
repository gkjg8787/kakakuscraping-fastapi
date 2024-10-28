import os

from html_parser import surugaya_html_parse

other_fpath = os.path.dirname(__file__) + "/data/surugaya_other.html"
shiharai_fpath = os.path.dirname(__file__) + "/data/shiharai.html"
other_url = "https://www.suruga-ya.jp/product/other/128002938"
redirect_detail_fpath = (
    os.path.dirname(__file__) + "/data/surugaya_detail_redirect.html"
)


def test_surugaya_makepure_postage_storepostage():
    with open(other_fpath, encoding="utf-8") as fp:
        sp = surugaya_html_parse.SurugayaParse(fp, 1, "2023-12-21 00:00:01", other_url)
        assert sp.hasPostage()
        sppl = sp.getPostageList()
        for spp in sppl:
            if spp.storename == "トレジャーユニバース":
                assert len(spp.target_prefectures) == 0
                assert (
                    spp.campaign_msg
                    == "1000以上 2024/06/05 00:00 ～ 2099/01/01 23:59 1,001円未満 500～2,000円 2,001円未満 400～2,000円 3,001円未満 300～2,000円 3,001円以上 0～1,500円"
                )
                assert len(spp.terms) == 0
            if spp.storename == "駿河屋日本橋本館":
                assert len(spp.target_prefectures) == 0
                assert len(spp.campaign_msg) == 0
                assert len(spp.terms) == 0
            if spp.storename == "駿河屋 アルパーク北棟店":
                assert len(spp.target_prefectures) == 0
                assert (
                    spp.campaign_msg
                    == "キャンペーン 2023/08/26 00:00 ～ 2024/08/26 23:59 2,000円未満 500～1,200円 2,000円以上 送料無料"
                )
                assert len(spp.terms) == 1
                assert spp.terms[0].boundary == "2000<="
                assert spp.terms[0].postage == 0
            if spp.storename == "駿河屋":
                assert len(spp.target_prefectures) == 0
                assert (
                    spp.campaign_msg
                    == "1,000円未満 440円 1,500円未満 385円 1,500円以上 送料無料"
                )
                assert len(spp.terms) == 3
                assert spp.terms[0].boundary == "1000>"
                assert spp.terms[0].postage == 440
                assert spp.terms[1].boundary == "1000<=:1500>"
                assert spp.terms[1].postage == 385
                assert spp.terms[2].boundary == "1500<="
                assert spp.terms[2].postage == 0


def test_surugaya_makepure_postage_shopidinfo():
    with open(other_fpath, encoding="utf-8") as fp:
        sp = surugaya_html_parse.SurugayaParse(fp, 1, "2023-12-21 00:00:01", other_url)
        assert sp.hasShopIDInfo()
        sidinf = sp.getShopIDInfo()
        base_url = "https://www.suruga-ya.jp/shop/"
        for key, val in sidinf.items():
            if key == "駿河屋日本橋本館":
                assert val.storename == key
                assert val.shop_id == 200823
                assert val.url == base_url + "200823"
            if key == "駿河屋九州物流センター":
                assert val.storename == key
                assert val.shop_id == 400411
                assert val.url == base_url + "400411"
            if key == "ブックマーケット福島北店 Supported by 駿河屋":
                assert val.storename == key
                assert val.shop_id == 200997
                assert val.url == base_url + "200997"
            if key == "駿河屋 アルパーク北棟店":
                assert val.storename == key
                assert val.shop_id == 400469
                assert val.url == base_url + "400469"


def test_surugaya_shiharai_parse():
    with open(shiharai_fpath, encoding="utf-8") as fp:
        sp = surugaya_html_parse.SurugayaShiharaiParse(fp)
        for psp in sp.get_ParseStorePostage():
            assert psp.storename == "駿河屋"
            if "東京" in psp.target_prefectures:
                assert len(psp.target_prefectures) == 34 + 7 + 4
                assert len(psp.terms) == 2
                assert psp.terms[0].boundary == "5000>"
                assert psp.terms[0].postage == "240"
                assert psp.terms[1].boundary == "5000<="
                assert psp.terms[1].postage == "0"
                continue
            if "北海道" in psp.target_prefectures:
                assert len(psp.target_prefectures) == 2
                assert len(psp.terms) == 3
                assert psp.terms[0].boundary == "5000>"
                assert psp.terms[0].postage == "570"
                assert psp.terms[1].boundary == "5000<=:10000>"
                assert psp.terms[1].postage == "285"
                assert psp.terms[2].boundary == "10000<="
                assert psp.terms[2].postage == "0"
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
        "created_at": "2024-10-28 10:30:00",
    }
    with open(redirect_detail_fpath, encoding="utf-8") as fp:
        sp = surugaya_html_parse.SurugayaParse(
            fp=fp,
            id=correct["url_id"],
            date=correct["created_at"],
            url=correct["url"],
        )
        for item in sp.getItems():
            for key, val in item.getOrderedDict().items():
                assert val == correct[key]

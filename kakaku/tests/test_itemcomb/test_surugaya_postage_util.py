from itemcomb import surugaya_postage_util as spu
from tests.test_db import test_db
from tests.test_sqlalchemy import delete_online_store_model


def test_convert_storename_to_search_storename():
    storename = "storename"
    answer = "answer"
    storename_dict_list = [
        {storename: "駿河屋日本橋本館", answer: "日本橋本館"},
        {storename: "ブックマーケット福島北店 Supported by 駿河屋", answer: "福島北"},
        {storename: "駿河屋 町田旭町店", answer: "町田旭町"},
        {storename: "駿河屋", answer: ""},
        {storename: "ブックエコ中間店", answer: "ブックエコ中間"},
    ]
    for sn_dic in storename_dict_list:
        ret = spu.convert_storename_to_search_storename(storename=sn_dic[storename])
        assert ret == sn_dic[answer]


def test_surugaya_postage_util_get_shippingResult_success(test_db):
    storename = "千葉中央"
    prefectures = ["東京都"]
    sres = spu.get_shippingResult(test_db, storename=storename, prefectures=prefectures)
    assert len(sres.get_list()) != 0
    for si in sres.get_list():
        assert 0 != si.get_prefecture_postage(prefectures[0])
        assert "千葉中央" in si.shop_name
        break
    delete_online_store_model(test_db)


def test_surugaya_postage_util_get_shippingResult_requests_ng(test_db, mocker):
    storename = "千葉中央"
    prefectures = ["東京都"]
    m = mocker.patch(
        "itemcomb.surugaya_postage_util.post_surugaya_postage.requests.post",
        side_effect=spu.post_surugaya_postage.Timeout,
    )
    sres = spu.get_shippingResult(test_db, storename=storename, prefectures=prefectures)
    assert len(sres.get_list()) != 0
    for si in sres.get_list():
        assert si.get_prefecture_postage(prefectures[0]) is None
        assert "千葉中央" in si.shop_name
        break
    delete_online_store_model(test_db)

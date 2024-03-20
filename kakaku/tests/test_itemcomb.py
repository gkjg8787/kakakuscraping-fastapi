import sys
import json
import logging

import pytest

from common import cmnlog, const_value as cmn_const_value
from itemcomb import sumitemcomb_adapt as sic_ada
from itemcomb import surugaya_postage_util as spu
from itemcomb import prefecture as ic_pref
from itemcomb import postage_data as posd
from accessor import store as ac_store

from tests.data import itemcomb_test_data
from tests.test_db import test_db
from tests.test_sqlalchemy import delete_online_store_model

ITEMLIST = "itemlist"
RESULT = "result"
STORECONF = "storeconf"
OUTTYPE = "json"


@pytest.fixture
def loginit():
    logger = logging.getLogger(cmnlog.LogName.ITEMCOMB)
    h = logging.StreamHandler(stream=sys.stdout)
    h.setFormatter(logging.Formatter(fmt="%(levelname)s - %(message)s"))
    logger.setLevel(logging.DEBUG)
    logger.addHandler(h)
    yield
    del logging.Logger.manager.loggerDict[logger.name]


def test_parse_boundary_of_Terms():
    from template_value.calcitemcomb import Terms
    from common.templates_string import HTMLOption

    t = Terms(
        terms_index=1,
        boundary="1500>:1000<=",
        postage="440",
        created_at="2023-01-01 00:00:00",
    )
    assert t.boundary1 == "1500"
    assert t.ope[0].lt == HTMLOption.SELECTED.value
    assert t.boundary2 == "1000"
    assert t.ope[1].ge == HTMLOption.SELECTED.value


def assert_itemlist_result(a: list, r: list):
    for aa in a:
        for rr in r:
            if aa["itemname"] != rr["itemname"]:
                continue
            assert aa["price"] == rr["price"]


def assert_searchcomb_result(a: dict, r: dict):
    for k, v in a.items():
        if k == "proc_time" or k == "errmsg":
            continue
        if isinstance(v, int):
            assert a[k] == r[k]
            continue
        if isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, int):
                    assert a[k][kk] == r[k][kk]
                    continue
                if isinstance(vv, list):
                    assert_itemlist_result(a[k][kk], r[k][kk])
        if isinstance(v, tuple):
            raise ValueError(f"v is tupple k={k}, v={v}")


def test_searchcomb_1(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_1
    return_dict = {
        "type": "fix",
        "value": "250",
        "min-value": "250",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_2(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_2
    return_dict = {
        "type": "fix",
        "value": "250",
        "min-value": "250",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_3(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_3
    return_dict = {
        "type": "fix",
        "value": "250",
        "min-value": "250",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_4(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_4
    return_dict = {
        "type": "fix",
        "value": "250",
        "min-value": "250",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_5(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_5
    return_dict = {
        "type": "fix",
        "value": "250",
        "min-value": "250",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_6_heavy(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_6
    return_dict = {
        "type": "fix",
        "value": "250",
        "min-value": "250",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_7_fix_margin_0(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_7
    return_dict = {
        "type": "fix",
        "value": "0",
        "min-value": "250",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_8_fix_margin_1(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_8
    return_dict = {
        "type": "fix",
        "value": "1",
        "min-value": "250",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_9_rate_margin_0_min_0(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_7
    return_dict = {
        "type": "rate",
        "value": "0",
        "min-value": "0",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_9_rate_margin_0_min_1(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_8
    return_dict = {
        "type": "rate",
        "value": "0",
        "min-value": "1",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_10_rate_margin_0_01_min_0(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_10
    return_dict = {
        "type": "rate",
        "value": "0.01",
        "min-value": "0",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_11_rate_margin_0_1_min_0(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_11
    return_dict = {
        "type": "rate",
        "value": "0.1",
        "min-value": "0",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_12_rate_margin_0_09_min_500(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_11
    return_dict = {
        "type": "rate",
        "value": "0.09",
        "min-value": "500",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_13_rate_margin_0_09_min_499(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_10
    return_dict = {
        "type": "rate",
        "value": "0.09",
        "min-value": "499",
    }
    m = mocker.patch(
        "itemcomb.sumitemcomb_adapt.get_itemcomb_price_margin", return_value=return_dict
    )
    ret = sic_ada.start_searchcomb(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
        exec_type=sic_ada.get_exec_itemcomb(),
    )
    assert_searchcomb_result(testcase[RESULT], ret)


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


def test_prefecture_PrefectureDBSetting_init_setting(test_db):
    try:
        ic_pref.PrefectureDBSetting.init_setting(test_db)
        ret = ac_store.PrefectureQuery.get_all(test_db)
        assert len(ret) == len(ic_pref.PrefectureName.get_all_prefecturename()) + 1
        pref_name_dic: dict[str, int] = {}
        for pref in ret:
            pref_name_dic[pref.name] = 1
            if pref.pref_id == cmn_const_value.NONE_PREF_ID:
                assert pref.name == ic_pref.PrefectureName.get_country_wide_name()
                continue
            assert pref.name in ic_pref.PrefectureName.get_all_prefecturename()
        assert len(pref_name_dic) == len(ret)
    finally:
        delete_online_store_model(test_db)


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


def assert_get_list_of_boundary_value_and_operation(
    boundary_text: str, result: list[dict]
):
    div_list = posd.ShippingTermsBoundary.get_list_of_boundary_value_and_operation(
        boundary_text
    )
    assert len(div_list) == len(result)
    for div, res in zip(div_list, result):
        assert div["boundary_ope"] == res["boundary_ope"]
        assert div["boundary_val"] == res["boundary_val"]


def test_postage_data_shipping_terms_boundary_get_list_of_boundary_value_and_operation_success_1():
    testdata = {"boundary": "0<", "result": [{"boundary_val": 0, "boundary_ope": "<"}]}
    assert_get_list_of_boundary_value_and_operation(
        testdata["boundary"], testdata["result"]
    )


def test_postage_data_shipping_terms_boundary_get_list_of_boundary_value_and_operation_success_2():
    testdata = {
        "boundary": "0<=:2000>",
        "result": [
            {"boundary_val": 0, "boundary_ope": "<="},
            {"boundary_val": 2000, "boundary_ope": ">"},
        ],
    }
    assert_get_list_of_boundary_value_and_operation(
        testdata["boundary"], testdata["result"]
    )


def test_postage_data_shipping_terms_boundary_get_list_of_boundary_value_and_operation_success_3():
    testdata = {
        "boundary": "300<:1500>=",
        "result": [
            {"boundary_val": 300, "boundary_ope": "<"},
            {"boundary_val": 1500, "boundary_ope": ">="},
        ],
    }
    assert_get_list_of_boundary_value_and_operation(
        testdata["boundary"], testdata["result"]
    )


def assert_add_terms_to_boundary(based: dict, addd: dict):
    base_boundary = posd.ShippingTermsBoundary.create_boundary_of_db(
        lower_ope=based["ope"], lower_val=based["val"]
    )
    assert based["result"] == base_boundary
    result = posd.ShippingTermsBoundary.add_terms_to_boundary(
        base_boundary, add_ope=addd["ope"], add_val=addd["val"]
    )
    assert addd["result"] == result


def test_postage_data_shipping_terms_boundary_add_terms_boundary_success_1():
    testdata = {
        "base": {"ope": "<", "val": 500, "result": "500<"},
        "add": {"ope": ">=", "val": 2000, "result": "500<:2000>="},
    }
    assert_add_terms_to_boundary(testdata["base"], testdata["add"])


def test_postage_data_shipping_terms_boundary_add_terms_boundary_success_2():
    testdata = {
        "base": {"ope": ">", "val": 2000, "result": "2000>"},
        "add": {"ope": "<=", "val": 700, "result": "700<=:2000>"},
    }
    assert_add_terms_to_boundary(testdata["base"], testdata["add"])


def test_postage_data_shipping_terms_boundary_add_terms_boundary_success_3():
    testdata = {
        "base": {"ope": "<=", "val": 0, "result": "0<="},
        "add": {"ope": ">=", "val": 1000, "result": "0<=:1000>="},
    }
    assert_add_terms_to_boundary(testdata["base"], testdata["add"])


def test_postage_data_shipping_terms_boundary_add_terms_boundary_ng_1():
    testdata = {
        "base": {"ope": ">", "val": 1000, "result": "1000>"},
        "add": {"ope": "<", "val": 1200, "result": "1000>"},
    }
    assert_add_terms_to_boundary(testdata["base"], testdata["add"])


def test_postage_data_shipping_terms_boundary_add_terms_boundary_ng_2():
    testdata = {
        "base": {"ope": ">", "val": 1000, "result": "1000>"},
        "add": {"ope": ">", "val": 500, "result": "500>"},
    }
    assert_add_terms_to_boundary(testdata["base"], testdata["add"])


def test_postage_data_shipping_terms_boundary_add_terms_boundary_ng_3():
    testdata = {
        "base": {"ope": "<", "val": 1800, "result": "1800<"},
        "add": {"ope": "<=", "val": 1500, "result": "1800<"},
    }
    assert_add_terms_to_boundary(testdata["base"], testdata["add"])

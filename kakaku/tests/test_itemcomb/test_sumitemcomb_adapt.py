import sys
import logging

import pytest

from common import cmnlog
from itemcomb import sumitemcomb_adapt as sic_ada

from tests.data import itemcomb_test_data
from tests.test_db import test_db


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

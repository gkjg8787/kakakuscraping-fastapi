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

    ret = sic_ada.call_get_itemcomb_with_pulp(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_2(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_2

    ret = sic_ada.call_get_itemcomb_with_pulp(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_3(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_3

    ret = sic_ada.call_get_itemcomb_with_pulp(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_4(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_4

    ret = sic_ada.call_get_itemcomb_with_pulp(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_5(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_5

    ret = sic_ada.call_get_itemcomb_with_pulp(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_6_heavy(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_6

    ret = sic_ada.call_get_itemcomb_with_pulp(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_8_fix_margin_1(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_8

    ret = sic_ada.call_get_itemcomb_with_pulp(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_9_rate_margin_0_min_1(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_8

    ret = sic_ada.call_get_itemcomb_with_pulp(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_11_rate_margin_0_1_min_0(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_11

    ret = sic_ada.call_get_itemcomb_with_pulp(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_searchcomb_12_rate_margin_0_09_min_500(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_11

    ret = sic_ada.call_get_itemcomb_with_pulp(
        storeconf=testcase[STORECONF],
        itemlist=testcase[ITEMLIST],
    )
    assert_searchcomb_result(testcase[RESULT], ret)


def test_convert_shipping_rules_1(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_1
    ret = sic_ada.convert_shipping_rules(conf=testcase[STORECONF])
    assert ret == {
        "静岡本店": [(0, 300)],
        "駿河屋": [
            (0, 440 + 240),  # 1000未満（1000>）と解釈
            (1000, 385 + 240),  # 1000以上（1000<=）と解釈
            (1500, 240),  # 1500以上
            (5000, 0),  # 5000以上
        ],
        "函館美原": [(0, 600)],
        "室蘭弥生": [(0, 600)],
        "ネットオフ": [(0, 440), (1500, 0)],
        "うねめ通り": [(0, 300)],
        "いわき平": [(0, 300)],
        "日本橋": [(0, 300)],
        "名古屋大須": [(0, 300)],
        "高槻": [(0, 350)],
        "福島北": [(0, 300)],
        "利府": [(0, 300)],
        "秋葉原本館": [(0, 300)],
        "千葉中央": [(0, 300)],
        "南瀬名": [(0, 350)],
        "宇都宮": [(0, 400)],
    }


def test_convert_shipping_rules_7(loginit, mocker):
    testcase = itemcomb_test_data.item_list_case_7
    ret = sic_ada.convert_shipping_rules(conf=testcase[STORECONF])
    assert ret == {
        "storeA": [(0, 500)],
        "storeB": [(0, 500), (2000, 0)],
    }

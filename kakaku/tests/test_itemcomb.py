import sys
import json
import logging

import pytest

from common import cmnlog
from itemcomb import sumitemcomb_adapt as sic_ada
from tests.data import itemcomb_test_data


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
    t = Terms(terms_index=1,
          boundary="1500>:1000<=",
          postage="440",
          created_at="2023-01-01 00:00:00")
    assert t.boundary1 == "1500"
    assert t.ope[0].lt == HTMLOption.SELECTED.value
    assert t.boundary2 == "1000"
    assert t.ope[1].ge == HTMLOption.SELECTED.value

def assert_itemlist_result(a :list, r :list):
    for aa in a:
        for rr in r:
            if aa["itemname"] != rr["itemname"]:
                continue
            assert aa["price"] == rr["price"]
                
def assert_searchcomb_result(a :dict, r :dict):
    for k,v in a.items():
        if k == "proc_time"\
            or k == "errmsg":
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



def test_searchcomb_1(loginit):
    testcase = itemcomb_test_data.item_list_case_1
    ret = sic_ada.start_searchcomb(
                    storeconf=testcase[STORECONF],
                    itemlist=testcase[ITEMLIST],
                    exec_type=sic_ada.get_exec_itemcomb(),
                    )
    assert_searchcomb_result(testcase[RESULT], ret)

def test_searchcomb_2(loginit):
    testcase = itemcomb_test_data.item_list_case_2
    ret = sic_ada.start_searchcomb(
                    storeconf=testcase[STORECONF],
                    itemlist=testcase[ITEMLIST],
                    exec_type=sic_ada.get_exec_itemcomb(),
                    )
    assert_searchcomb_result(testcase[RESULT], ret)

def test_searchcomb_3(loginit):
    testcase = itemcomb_test_data.item_list_case_3
    ret = sic_ada.start_searchcomb(
                    storeconf=testcase[STORECONF],
                    itemlist=testcase[ITEMLIST],
                    exec_type=sic_ada.get_exec_itemcomb(),
                    )
    assert_searchcomb_result(testcase[RESULT], ret)

def test_searchcomb_4(loginit):
    testcase = itemcomb_test_data.item_list_case_4
    ret = sic_ada.start_searchcomb(
                    storeconf=testcase[STORECONF],
                    itemlist=testcase[ITEMLIST],
                    exec_type=sic_ada.get_exec_itemcomb(),
                    )
    assert_searchcomb_result(testcase[RESULT], ret)

def test_searchcomb_5(loginit):
    testcase = itemcomb_test_data.item_list_case_5
    ret = sic_ada.start_searchcomb(
                    storeconf=testcase[STORECONF],
                    itemlist=testcase[ITEMLIST],
                    exec_type=sic_ada.get_exec_itemcomb(),
                    )
    assert_searchcomb_result(testcase[RESULT], ret)

def test_searchcomb_6_heavy(loginit):
    testcase = itemcomb_test_data.item_list_case_6
    ret = sic_ada.start_searchcomb(
                    storeconf=testcase[STORECONF],
                    itemlist=testcase[ITEMLIST],
                    exec_type=sic_ada.get_exec_itemcomb(),
                    )
    assert_searchcomb_result(testcase[RESULT], ret)
    
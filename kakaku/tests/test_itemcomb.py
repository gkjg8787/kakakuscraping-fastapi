import json

from itemcomb import sumitemcomb


from tests.data import itemcomb_test_data


ITEMLIST = "itemlist"
RESULT = "result"
STORECONF = "storeconf"
OUTTYPE = "json"



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


def test_searchcomb_1():
    testcase = itemcomb_test_data.item_list_case_1
    ret = sumitemcomb.searchcomb(
                            storeconf=testcase[STORECONF],
                            itemlist=testcase[ITEMLIST],
                            outf=OUTTYPE
                            )
    assert json.loads(ret) == testcase[RESULT]

def test_searchcomb_2():
    testcase = itemcomb_test_data.item_list_case_2
    ret = sumitemcomb.searchcomb(
                            storeconf=testcase[STORECONF],
                            itemlist=testcase[ITEMLIST],
                            outf=OUTTYPE
                            )
    assert json.loads(ret) == testcase[RESULT]

def test_searchcomb_3():
    testcase = itemcomb_test_data.item_list_case_3
    ret = sumitemcomb.searchcomb(
                            storeconf=testcase[STORECONF],
                            itemlist=testcase[ITEMLIST],
                            outf=OUTTYPE
                            )
    assert json.loads(ret) == testcase[RESULT]

def test_searchcomb_4():
    testcase = itemcomb_test_data.item_list_case_4
    ret = sumitemcomb.searchcomb(
                            storeconf=testcase[STORECONF],
                            itemlist=testcase[ITEMLIST],
                            outf=OUTTYPE
                            )
    assert json.loads(ret) == testcase[RESULT]
    
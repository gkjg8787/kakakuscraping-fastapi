from common.filter_name import FilterQueryName, FilterOnOff
from url_search import sitesearch

def test_get_search_for_inner_surugaya():
    sword = "ジブリ"
    query_opt = {
        FilterQueryName.PAGE.value: 1,
        FilterQueryName.STORE.value:[1],
        FilterQueryName.CATEGORY.value:3,
        FilterQueryName.ZAIKO.value:0,
        FilterQueryName.SAFES.value: FilterOnOff.ON,
        "output":{"type":"text"},
    }
    resdic = sitesearch.get_search_for_inner(sword=sword, optdict=query_opt)
    assert len(resdic) != 0
    assert 'result' in resdic
    assert len(resdic['result']['items']) != 0
    print(resdic['result'])

def test_get_search_for_inner_geo():
    sword = "となりのトトロ"
    query_opt = {
        FilterQueryName.PAGE.value: 1,
        FilterQueryName.STORE.value:[4],
        FilterQueryName.CATEGORY.value:3,
        FilterQueryName.ZAIKO.value:0,
        FilterQueryName.SAFES.value: FilterOnOff.ON,
        "output":{"type":"text"},
    }
    resdic = sitesearch.get_search_for_inner(sword=sword, optdict=query_opt)
    assert len(resdic) != 0
    assert 'result' in resdic
    assert len(resdic['result']['items']) != 0
    print(resdic['result'])







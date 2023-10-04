
from analysis import database_analysis as dbana

from tests.data import analysis_test_data as test_data



def test_sqlalchemy_result_all_to_dict_list():
    data = test_data.get_one_week_data()
    dict_list = dbana.sqlalchemy_result_all_to_dict_list(data)
    ans = test_data.get_one_week_dict()
    ans_url_id_dict = {}
    for a in ans:
        if a["url_id"] in ans_url_id_dict:
            ans_url_id_dict[a["url_id"]].append(a)
        else:
            ans_url_id_dict[a["url_id"]] = [a]
    
    for dic in dict_list:
        assert dic["url_id"] in ans_url_id_dict
        is_exist = False
        for a in ans_url_id_dict[dic["url_id"]]:
            if a["created_at"] == dic["created_at"]\
                and a["item_id"] == dic["item_id"]\
                and a["usedprice"] == dic["usedprice"]\
                and a["newprice"] == dic["newprice"]:
                is_exist = True
        assert is_exist == True

def test_get_period_end_datetime():
    data = test_data.get_one_week_data()
    dict_list = dbana.sqlalchemy_result_all_to_dict_list(data)
    st, et = dbana.LogAnalysis.get_period_end_datetime(dict_list)
    assert st == test_data.one_week_ago
    assert et == test_data.now

def test_get_period_end_itemid_and_urlid():
    data = test_data.get_one_week_data()
    dict_list = dbana.sqlalchemy_result_all_to_dict_list(data)
    st, et = dbana.LogAnalysis.get_period_end_datetime(dict_list)
    result = dbana.LogAnalysis.get_period_end_itemid_and_urlid(
        dict_list=dict_list,
        start_datetime=st,
        end_datetime=et,
    )
    keyName = dbana.AnalysisKeyName
    assert keyName.PERIOD_ITEMID in result
    assert len(result[keyName.PERIOD_ITEMID][keyName.START][keyName.ACT]) == 4
    assert len(result[keyName.PERIOD_ITEMID][keyName.START][keyName.INACT]) == 0
    assert len(result[keyName.PERIOD_ITEMID][keyName.END][keyName.ACT]) == 4
    assert len(result[keyName.PERIOD_ITEMID][keyName.END][keyName.INACT]) == 0
    assert len(result[keyName.PERIOD_ITEMID][keyName.COMMON][keyName.ACT]) == 4
    
    assert len(result[keyName.PERIOD_URLID][keyName.START][keyName.ACT]) == 4
    assert len(result[keyName.PERIOD_URLID][keyName.START][keyName.INACT]) == 0
    assert len(result[keyName.PERIOD_URLID][keyName.END][keyName.ACT]) == 4
    assert len(result[keyName.PERIOD_URLID][keyName.END][keyName.INACT]) == 0
    assert len(result[keyName.PERIOD_URLID][keyName.COMMON][keyName.ACT]) == 4

def test_get_period_end_log():
    data = test_data.get_one_week_data()
    dict_list = dbana.sqlalchemy_result_all_to_dict_list(data)
    st, et = dbana.LogAnalysis.get_period_end_datetime(dict_list)
    result = dbana.LogAnalysis.get_period_end_log(
            dict_list=dict_list,
            start_datetime=st,
            end_datetime=et,
    )
    keyName = dbana.AnalysisKeyName
    assert len(result[keyName.PERIOD_LOG][keyName.START]) == 5
    assert len(result[keyName.PERIOD_LOG][keyName.END]) == 5

def test_DaysItemLog():
    data = test_data.get_one_week_data()
    dict_list = dbana.sqlalchemy_result_all_to_dict_list(data)
    st, et = dbana.LogAnalysis.get_period_end_datetime(dict_list)

    period_end_log = dbana.LogAnalysis.get_period_end_log(
            dict_list=dict_list,
            start_datetime=st,
            end_datetime=et,
    )
    keyName = dbana.AnalysisKeyName
    start_dil = dbana.DaysItemLog(dict_list=period_end_log[keyName.PERIOD_LOG][keyName.START])
    assert start_dil.get_lowest_price_in_item(1) == 1500
    assert start_dil.get_lowest_price_in_item(2) == 1200
    assert start_dil.get_lowest_price_in_item(3) == 3000
    assert start_dil.get_lowest_price_in_item(4) == 3300

    end_dil = dbana.DaysItemLog(dict_list=period_end_log[keyName.PERIOD_LOG][keyName.END])
    assert end_dil.get_lowest_price_in_item(1) == 1400
    assert end_dil.get_lowest_price_in_item(2) == 1000
    assert end_dil.get_lowest_price_in_item(3) == 3300
    assert end_dil.get_lowest_price_in_item(4) == 3600

def test_get_item_price_analysis():
    data = test_data.get_one_week_data()
    dict_list = dbana.sqlalchemy_result_all_to_dict_list(data)
    st, et = dbana.LogAnalysis.get_period_end_datetime(dict_list)
    convertdata = dbana.LogAnalysis.get_period_end_itemid_and_urlid(
        dict_list=dict_list,
        start_datetime=st,
        end_datetime=et,
    )
    period_end_log = dbana.LogAnalysis.get_period_end_log(
            dict_list=dict_list,
            start_datetime=st,
            end_datetime=et,
    )
    keyName = dbana.AnalysisKeyName
    result = dbana.LogAnalysis.get_item_price_analysis(
            common_ids=convertdata[keyName.PERIOD_ITEMID][keyName.COMMON][keyName.ACT],
            start_data=period_end_log[keyName.PERIOD_LOG][keyName.START],
            end_data=period_end_log[keyName.PERIOD_LOG][keyName.END],
        )
    assert result[keyName.START][keyName.INIT_PRICE_COUNT] == 0
    assert result[keyName.END][keyName.INIT_PRICE_COUNT] == 0
    assert len(result[keyName.PRICE][keyName.UP]) == 2
    assert len(result[keyName.PRICE][keyName.DOWN]) == 2
    assert len(result[keyName.PRICE][keyName.NO_CHANGE]) == 0
    
    
from datetime import datetime, timedelta

from accessor.item.item import AnalysisQuery
from common.util import utcTolocaltime

from tests.test_accessor import db_test_data
from tests.test_db import test_db
from tests.test_sqlalchemy import (
    delete_item_model,
)

def test_get_itemlog_from_day(test_db):
    days = -7
    db_test_data.add_analysis_data_set_1(test_db)
    result = AnalysisQuery.get_itemlog_from_day(test_db, days=days)
    res_dic = {}
    for r in result:
        #url_id毎
        if r[1] in res_dic:
            res_dic[r[1]].append(r)
        else:
            res_dic[r[1]] = [r]
    print(res_dic)
    assert len(res_dic[1]) == 3
    assert len(res_dic[2]) == 6
    assert len(res_dic[3]) == 3
    assert len(res_dic[4]) == 3
    
    delete_item_model(test_db)

def test_get_itemlog_start_and_end_from_day(test_db):
    days = -7
    db_test_data.add_analysis_data_set_1(test_db)
    result = AnalysisQuery.get_itemlog_period_datetime_from_day(test_db, days=days)
    print(result)
    one_week_ago = datetime.utcnow() + timedelta(days=days)
    assert result[0][0].date() == one_week_ago.date()
    assert result[0][1].date() == datetime.utcnow().date()
    
    delete_item_model(test_db)

def test_get_itemlog_by_period_date(test_db):
    days = -7
    db_test_data.add_analysis_data_set_1(test_db)
    one_week_ago_jst = utcTolocaltime(datetime.utcnow() + timedelta(days=days))
    now_jst = utcTolocaltime(datetime.utcnow())
    result = AnalysisQuery.get_itemlog_by_period_date(test_db,
                                                      start_jst=one_week_ago_jst.date(),
                                                      end_jst=now_jst.date()
                                                      )
    res_dic = {}
    for r in result:
        #url_id毎
        if r[1] in res_dic:
            res_dic[r[1]].append(r)
        else:
            res_dic[r[1]] = [r]
    print(res_dic)
    assert len(res_dic[1]) == 2
    assert len(res_dic[2]) == 4
    assert len(res_dic[3]) == 2
    assert len(res_dic[4]) == 2
    
    delete_item_model(test_db)

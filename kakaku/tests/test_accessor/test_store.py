from datetime import datetime, timedelta

from accessor import store
from itemcomb.prefecture import PrefectureDBSetting
from itemcomb import postage_data as posd

from tests.test_db import test_db
from tests.test_accessor import db_test_data
from tests.test_sqlalchemy import (
    delete_online_store_model,
    delete_item_and_store_model,
    delete_item_model,
    delete_store_model,
)

def test_online_store_get_todays_storenames(test_db):
    db_test_data.add_online_store_data_set_of_pricelog(test_db)
    ret = store.OnlineStoreQuery.get_todays_storenames(db=test_db)
    assert len(ret) == 3
    assert db_test_data.SURUGAYA in ret
    assert db_test_data.SURUGAYA_CHIBA in ret
    assert db_test_data.NETOFF in ret
    delete_item_model(test_db)

def test_online_store_delete_postage_by_not_in_storename_list(test_db):
    PrefectureDBSetting.init_setting(test_db)
    db_test_data.add_online_store_data_set_1(test_db)
    sn_list = [db_test_data.SURUGAYA, db_test_data.GEO]
    store.OnlineStoreQuery.delete_postage_by_not_in_storename_list(db=test_db, storename_list=sn_list)
    ret = store.OnlineStoreQuery.get_all(test_db)
    for r in ret:
        dic = dict(r._mapping.items())
        if dic["storename"] in sn_list:
            assert dic["pref_id"] is not None
            assert dic["boundary"] is not None
            assert dic["postage"] is not None
        else:
            assert dic["pref_id"] is None
            assert dic["boundary"] is None
    delete_online_store_model(test_db)

def test_daily_online_shop_info_delete_insert_proc_type_1(test_db):
    db_test_data.add_daily_online_shop_data_set_1(test_db)
    cnt = store.DailyOnlineShopInfoQuery.get_todays_count(db=test_db)
    assert cnt == 3
    store.DailyOnlineShopInfoQuery.delete(db=test_db,
                                          insert_proc_type_list=[posd.InsertProcType.ITEM_UPDATE.value]
                                          )
    ret = store.DailyOnlineShopInfoQuery.get_all(db=test_db)
    assert len(ret) == 2
    for r in ret:
        assert r.shop_id != 400395
    delete_online_store_model(test_db)

def test_daily_online_shop_info_get_count_before_today(test_db):
    db_test_data.add_daily_online_shop_data_set_1(test_db)
    assert 0 == store.DailyOnlineShopInfoQuery.get_count_before_today(test_db)
    ret = store.DailyOnlineShopInfoQuery.get_all(test_db)
    up_list = []
    for a in ret:
        a.created_at = a.created_at - timedelta(days=1)
        up_list.append(a)
        break
    store.DailyOnlineShopInfoQuery.update(db=test_db,
                                          update_list=up_list
                                          )
    assert 1 == store.DailyOnlineShopInfoQuery.get_count_before_today(test_db)
    delete_online_store_model(test_db)

def test_daily_online_shop_info_get_by_contains_storename(test_db):
    db_test_data.add_daily_online_shop_data_set_1(test_db)
    storename = "千葉"
    ret = store.DailyOnlineShopInfoQuery.get_by_contains_storename(test_db, storename=storename)
    assert len(ret) == 1
    assert ret[0].shop_id == 400407
    delete_online_store_model(test_db)

    



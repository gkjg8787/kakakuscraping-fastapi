

from common import filter_name
from common.util import dbtimeTodatetime

from accessor.item import (
    NewestQuery,
)
from tests.test_sqlalchemy import (
    delete_item_model,
    delete_item_and_store_model,
)

from tests.test_db import test_db

from tests.test_accessor.db_test_data import add_data_set_1, add_data_set_1_plus_store



def test_get_newest_data_no_data_filter_none(test_db):
    filter_dict = {}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

###############################
# GROUP ID Filter
###############################
def test_get_newest_data_no_data_filter_group_id(test_db):
    filter_dict = {filter_name.FilterQueryName.GID.value:1}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_no_data_filter_group_id(test_db):
    filter_dict = {filter_name.FilterQueryName.GID.value:1}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_no_data_filter_bad_group_id(test_db):
    filter_dict = {filter_name.FilterQueryName.GID.value:-1}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

###############################
# ACT Filter
###############################
def test_get_newest_data_no_data_filter_active(test_db):
    filter_dict = {filter_name.FilterQueryName.ACT.value:filter_name.ActFilterName.ACT.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_no_data_filter_inactive(test_db):
    filter_dict = {filter_name.FilterQueryName.ACT.value:filter_name.ActFilterName.INACT.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_no_data_filter_all(test_db):
    filter_dict = {filter_name.FilterQueryName.ACT.value:filter_name.ActFilterName.ALL.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_exist_data_filter_active(test_db):
    add_data_set_1(test_db)
    filter_dict = {filter_name.FilterQueryName.ACT.value:filter_name.ActFilterName.ACT.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 7
    delete_item_model(test_db)

def test_get_newest_data_exist_data_filter_inactive(test_db):
    add_data_set_1(test_db)
    filter_dict = {filter_name.FilterQueryName.ACT.value:filter_name.ActFilterName.INACT.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 1
    delete_item_model(test_db)

def test_get_newest_data_exist_data_filter_all(test_db):
    add_data_set_1(test_db)
    filter_dict = {filter_name.FilterQueryName.ACT.value:filter_name.ActFilterName.ALL.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    delete_item_model(test_db)

###############################
# STORENAME Filter
###############################
def test_get_newest_data_no_data_filter_storename(test_db):
    filter_dict = {filter_name.FilterQueryName.STORE.value:1}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_no_data_filter_storename_no_length(test_db):
    filter_dict = {filter_name.FilterQueryName.STORE.value:-1}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_exist_data_filter_storename(test_db):
    add_data_set_1_plus_store(test_db)
    filter_dict = {filter_name.FilterQueryName.STORE.value:1}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 5
    delete_item_and_store_model(test_db)

###############################
# ItemSort Filter
###############################
def test_get_newest_data_no_data_filter_isort_old_item(test_db):
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.OLD_ITEM.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_exist_data_filter_isort_old_item(test_db):
    add_data_set_1(test_db)
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.OLD_ITEM.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    old_id = None
    for res in results:
        dic = { k:y for k,y in res._mapping.items()}
        if not old_id:
            old_id = int(dic["item_id"])
            continue
        if old_id:
            assert old_id < int(dic["item_id"])
            old_id = int(dic["item_id"])
            continue
    delete_item_model(test_db)

def test_get_newest_data_no_data_filter_isort_new_item(test_db):
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.NEW_ITEM.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_exist_data_filter_isort_new_item(test_db):
    add_data_set_1(test_db)
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.NEW_ITEM.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    new_id = None
    for res in results:
        dic = { k:y for k,y in res._mapping.items()}
        if not new_id:
            new_id = int(dic["item_id"])
            continue
        if new_id:
            assert new_id > int(dic["item_id"])
            new_id = int(dic["item_id"])
            continue
    delete_item_model(test_db)

def test_get_newest_data_no_data_filter_isort_low_price(test_db):
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.LOW_PRICE.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_exist_data_filter_isort_low_price(test_db):
    add_data_set_1(test_db)
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.LOW_PRICE.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    price = None
    for res in results:
        dic = { k:y for k,y in res._mapping.items()}
        if not price:
            price = int(dic["price"])
            continue
        if price:
            assert price <= int(dic["price"])
            price = int(dic["price"])
            continue
    delete_item_model(test_db)

def test_get_newest_data_no_data_filter_isort_high_price(test_db):
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.HIGH_PRICE.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_exist_data_filter_isort_high_price(test_db):
    add_data_set_1(test_db)
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.HIGH_PRICE.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    price = None
    for res in results:
        dic = { k:y for k,y in res._mapping.items()}
        if not price:
            price = int(dic["price"])
            continue
        if price:
            assert price >= int(dic["price"])
            price = int(dic["price"])
            continue
    delete_item_model(test_db)

def test_get_newest_data_no_data_filter_isort_item_name(test_db):
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.ITEM_NAME.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_no_data_filter_isort_store_name(test_db):
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.STORE_NAME.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_no_data_filter_isort_low_trendrate(test_db):
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.LOW_TRENDRATE.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_exist_data_filter_isort_low_trendrate(test_db):
    add_data_set_1(test_db)
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.LOW_TRENDRATE.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    rate = None
    for res in results:
        dic = { k:y for k,y in res._mapping.items()}
        if not rate:
            rate = float(dic["trendrate"])
            continue
        if rate:
            assert rate <= float(dic["trendrate"])
            rate = float(dic["trendrate"])
            continue
    delete_item_model(test_db)

def test_get_newest_data_no_data_filter_isort_high_trendrate(test_db):
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.HIGH_TRENDRATE.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_no_data_filter_isort_high_trendrate(test_db):
    add_data_set_1(test_db)
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.HIGH_TRENDRATE.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    rate = None
    for res in results:
        dic = { k:y for k,y in res._mapping.items()}
        if not rate:
            rate = float(dic["trendrate"])
            continue
        if rate:
            assert rate >= float(dic["trendrate"])
            rate = float(dic["trendrate"])
            continue
    delete_item_model(test_db)

def test_get_newest_data_no_data_filter_isort_new_update_time(test_db):
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.NEW_UPDATE_TIME.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0

def test_get_newest_data_no_data_filter_isort_new_update_time(test_db):
    add_data_set_1(test_db)
    filter_dict = {filter_name.FilterQueryName.ISORT.value:filter_name.ItemSortName.NEW_UPDATE_TIME.id}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    uptime = None
    for res in results:
        dic = { k:y for k,y in res._mapping.items()}
        if not uptime:
            uptime = dbtimeTodatetime(dic["created_at"])
            continue
        if uptime:
            assert uptime >= dbtimeTodatetime(dic["created_at"])
            uptime = dbtimeTodatetime(dic["created_at"])
            continue
    delete_item_model(test_db)

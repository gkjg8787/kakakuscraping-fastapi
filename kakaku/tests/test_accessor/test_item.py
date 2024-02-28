from common import filter_name
from common.util import dbtimeTodatetime
from common import const_value
from accessor.item import (
    NewestQuery,
    ItemQuery,
    UrlQuery,
)
from tests.test_sqlalchemy import (
    delete_item_model,
    delete_item_and_store_model,
)

from tests.test_db import test_db

from tests.test_accessor.db_test_data import (
    add_data_set_1,
    add_data_set_1_plus_store,
    add_data_set_2,
    add_data_set_3,
    add_data_set_4,
    add_extract_store_data_set_1,
)


def test_get_newest_data_no_data_filter_none(test_db):
    filter_dict = {}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


###############################
# GROUP ID Filter
###############################
def test_get_newest_data_no_data_filter_group_id(test_db):
    filter_dict = {filter_name.FilterQueryName.GID.value: 1}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_no_data_filter_group_id(test_db):
    filter_dict = {filter_name.FilterQueryName.GID.value: 1}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_no_data_filter_bad_group_id(test_db):
    filter_dict = {filter_name.FilterQueryName.GID.value: -1}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


###############################
# ACT Filter
###############################
def test_get_newest_data_no_data_filter_active(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.ACT.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_no_data_filter_inactive(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.INACT.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_no_data_filter_all(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.ALL.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_active(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.ACT.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 7
    delete_item_model(test_db)


def test_get_newest_data_exist_data_filter_inactive(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.INACT.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 1
    delete_item_model(test_db)


def test_get_newest_data_exist_data_filter_all(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.ALL.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    delete_item_model(test_db)


###############################
# ZAIKO Filter
###############################


def test_get_newest_data_exist_data_filter_zaiko_on(test_db):
    add_data_set_1(test_db)
    filter_dict = {filter_name.FilterQueryName.ZAIKO.value: filter_name.FilterOnOff.ON}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 7
    delete_item_model(test_db)


def test_get_newest_data_exist_data_filter_zaiko_off(test_db):
    add_data_set_1(test_db)
    filter_dict = {filter_name.FilterQueryName.ZAIKO.value: filter_name.FilterOnOff.OFF}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    delete_item_model(test_db)


def test_get_newest_data_exist_data_filter_zaiko_other(test_db):
    add_data_set_1(test_db)
    other_value = 8
    filter_dict = {filter_name.FilterQueryName.ZAIKO.value: other_value}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    delete_item_model(test_db)


###############################
# STORENAME Filter
###############################
def test_get_newest_data_no_data_filter_storename(test_db):
    filter_dict = {filter_name.FilterQueryName.STORE.value: 1}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_no_data_filter_storename_no_length(test_db):
    filter_dict = {filter_name.FilterQueryName.STORE.value: -1}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_storename(test_db):
    add_data_set_1_plus_store(test_db)
    filter_dict = {filter_name.FilterQueryName.STORE.value: 1}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 5
    delete_item_and_store_model(test_db)


###############################
# ItemSort Filter
###############################
def test_get_newest_data_no_data_filter_isort_old_item(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.OLD_ITEM.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_isort_old_item(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.OLD_ITEM.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    old_id = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not old_id:
            old_id = int(dic["item_id"])
            continue
        if old_id:
            assert old_id < int(dic["item_id"])
            old_id = int(dic["item_id"])
            continue
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_isort_new_item(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.NEW_ITEM.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_isort_new_item(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.NEW_ITEM.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    new_id = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not new_id:
            new_id = int(dic["item_id"])
            continue
        if new_id:
            assert new_id > int(dic["item_id"])
            new_id = int(dic["item_id"])
            continue
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_isort_low_price(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.LOW_PRICE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_isort_low_price(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.LOW_PRICE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    price = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not price:
            price = int(dic["price"])
            continue
        if price:
            assert price <= int(dic["price"])
            price = int(dic["price"])
            continue
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_isort_high_price(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.HIGH_PRICE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_isort_high_price(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.HIGH_PRICE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    price = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not price:
            price = int(dic["price"])
            continue
        if price:
            assert price >= int(dic["price"])
            price = int(dic["price"])
            continue
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_isort_item_name(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.ITEM_NAME.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_no_data_filter_isort_store_name(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.STORE_NAME.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_no_data_filter_isort_low_trendrate(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.LOW_TRENDRATE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_isort_low_trendrate(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.LOW_TRENDRATE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    rate = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not rate:
            rate = float(dic["trendrate"])
            continue
        if rate:
            assert rate <= float(dic["trendrate"])
            rate = float(dic["trendrate"])
            continue
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_isort_high_trendrate(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.HIGH_TRENDRATE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_isort_high_trendrate(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.HIGH_TRENDRATE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    rate = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not rate:
            rate = float(dic["trendrate"])
            continue
        if rate:
            assert rate >= float(dic["trendrate"])
            rate = float(dic["trendrate"])
            continue
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_isort_old_update_time(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.OLD_UPDATE_TIME.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_isort_old_update_time(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.OLD_UPDATE_TIME.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    uptime = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not uptime:
            uptime = dbtimeTodatetime(dic["created_at"])
            continue
        if uptime:
            assert uptime <= dbtimeTodatetime(dic["created_at"])
            uptime = dbtimeTodatetime(dic["created_at"])
            continue
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_isort_new_update_time(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.NEW_UPDATE_TIME.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_isort_new_update_time(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.NEW_UPDATE_TIME.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    uptime = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not uptime:
            uptime = dbtimeTodatetime(dic["created_at"])
            continue
        if uptime:
            assert uptime >= dbtimeTodatetime(dic["created_at"])
            uptime = dbtimeTodatetime(dic["created_at"])
            continue
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_isort_low_lowest_price(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.LOW_LOWESTPRICE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_isort_low_lowest_price(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.LOW_LOWESTPRICE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    price = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not price:
            price = int(dic["lowestprice"])
            continue
        if price:
            assert price <= int(dic["lowestprice"])
            price = int(dic["lowestprice"])
            continue
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_isort_high_lowest_price(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.HIGH_LOWESTPRICE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_isort_high_lowest_price(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.HIGH_LOWESTPRICE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    price = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not price:
            price = int(dic["lowestprice"])
            continue
        if price:
            assert price >= int(dic["lowestprice"])
            price = int(dic["lowestprice"])
            continue
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_isort_closest_lowest_price(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.CLOSEST_LOWESTPRICE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_isort_closest_lowest_price(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.CLOSEST_LOWESTPRICE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 7

    def get_compare_val(dic: dict):
        return int(dic["price"]) - int(dic["lowestprice"])

    pre_diff = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not pre_diff:
            pre_diff = get_compare_val(dic)
            continue
        if pre_diff:
            assert pre_diff <= get_compare_val(dic)
            pre_diff = get_compare_val(dic)
            continue
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_isort_furthest_lowest_price(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.FURTHEST_LOWESTPRICE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_isort_furthest_lowest_price(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ISORT.value: filter_name.ItemSortName.FURTHEST_LOWESTPRICE.id
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 7

    def get_compare_val(dic: dict):
        return int(dic["price"]) - int(dic["lowestprice"])

    pre_diff = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not pre_diff:
            pre_diff = get_compare_val(dic)
            continue
        if pre_diff:
            assert pre_diff >= get_compare_val(dic)
            pre_diff = get_compare_val(dic)
            continue
    delete_item_model(test_db)


###############################
# Item Price Range Filter
###############################
def test_get_newest_data_no_data_filter_item_price_range_min(test_db):
    val = 0
    filter_dict = {filter_name.FilterQueryName.PRMIN.value: val}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_item_price_range_min(test_db):
    add_data_set_1(test_db)
    val = 0
    filter_dict = {filter_name.FilterQueryName.PRMIN.value: val}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 7
    delete_item_model(test_db)


def test_get_newest_data_exist_data_filter_item_price_range_min_bad_value(test_db):
    add_data_set_1(test_db)
    val = -2
    filter_dict = {filter_name.FilterQueryName.PRMIN.value: val}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_item_price_range_max(test_db):
    val = 0
    filter_dict = {filter_name.FilterQueryName.PRMAX.value: val}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_item_price_range_max(test_db):
    add_data_set_1(test_db)
    val = 3000
    filter_dict = {filter_name.FilterQueryName.PRMAX.value: val}
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 6
    delete_item_model(test_db)


def test_get_newest_data_no_data_filter_item_price_range_min_and_max(test_db):
    minv = 0
    maxv = 1
    filter_dict = {
        filter_name.FilterQueryName.PRMIN.value: minv,
        filter_name.FilterQueryName.PRMAX.value: maxv,
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_newest_data_exist_data_filter_item_price_range_min_and_max_eq(test_db):
    add_data_set_1(test_db)
    minv = 1500
    maxv = 1500
    filter_dict = {
        filter_name.FilterQueryName.PRMIN.value: minv,
        filter_name.FilterQueryName.PRMAX.value: maxv,
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 1
    delete_item_model(test_db)


def test_get_newest_data_exist_data_filter_item_price_range_min_and_max_range(test_db):
    add_data_set_1(test_db)
    minv = 1000
    maxv = 2000
    filter_dict = {
        filter_name.FilterQueryName.PRMIN.value: minv,
        filter_name.FilterQueryName.PRMAX.value: maxv,
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 4
    delete_item_model(test_db)


def test_get_newest_data_exist_data_filter_item_price_range_min_and_max_range_ng(
    test_db,
):
    add_data_set_1(test_db)
    minv = 1000
    maxv = 900
    filter_dict = {
        filter_name.FilterQueryName.PRMIN.value: minv,
        filter_name.FilterQueryName.PRMAX.value: maxv,
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 8
    delete_item_model(test_db)


def test_get_newest_data_exist_data_filter_item_price_range_min_and_max_min_ng(test_db):
    add_data_set_1(test_db)
    minv = -2
    maxv = 2000
    filter_dict = {
        filter_name.FilterQueryName.PRMIN.value: minv,
        filter_name.FilterQueryName.PRMAX.value: maxv,
    }
    results = NewestQuery.get_newest_data(test_db, filter=filter_dict)
    assert len(results) == 5
    delete_item_model(test_db)


###############################
# Item Comb list
###############################
def test_get_url_and_item_comb_list_no_data_filter_none(test_db):
    filter_dict = {}
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 0


###############################
# ACT Filter
###############################
def test_get_url_and_item_comb_list_no_data_filter_active(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.ACT.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 0


def test_get_url_and_item_comb_list_no_data_filter_inactive(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.INACT.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 0


def test_get_url_and_item_comb_list_no_data_filter_all(test_db):
    filter_dict = {
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.ALL.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 0


def test_get_url_and_item_comb_list_exist_data_filter_active(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.ACT.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 7
    delete_item_model(test_db)


def test_get_url_and_item_comb_list_exist_data_filter_inactive(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.INACT.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 1
    delete_item_model(test_db)


def test_get_url_and_item_comb_list_exist_data_filter_all(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.ALL.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 8
    delete_item_model(test_db)


###############################
# UrlSort Filter
###############################
def test_get_url_and_item_comb_list_no_data_filter_usort_urlid_asc(test_db):
    filter_dict = {
        filter_name.FilterQueryName.USORT.value: filter_name.UrlSortName.URLID_ASC.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 0


def test_get_url_and_item_comb_list_no_data_filter_usort_urlid_desc(test_db):
    filter_dict = {
        filter_name.FilterQueryName.USORT.value: filter_name.UrlSortName.URLID_DESC.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 0


def test_get_url_and_item_comb_list_no_data_filter_usort_itemid_asc(test_db):
    filter_dict = {
        filter_name.FilterQueryName.USORT.value: filter_name.UrlSortName.ITEMID_ASC.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 0


def test_get_url_and_item_comb_list_no_data_filter_usort_itemid_desc(test_db):
    filter_dict = {
        filter_name.FilterQueryName.USORT.value: filter_name.UrlSortName.ITEMID_DESC.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 0


def test_get_url_and_item_comb_list_no_data_filter_usort_urlid_asc(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.USORT.value: filter_name.UrlSortName.URLID_ASC.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 8
    id = -1
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        assert id <= dic["url_id"]
        id = dic["url_id"]
        continue

    delete_item_model(test_db)


def test_get_url_and_item_comb_list_no_data_filter_usort_urlid_desc(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.USORT.value: filter_name.UrlSortName.URLID_DESC.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 8
    id = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not id:
            id = dic["url_id"]
            continue
        assert id >= dic["url_id"]
        id = dic["url_id"]
        continue

    delete_item_model(test_db)


def test_get_url_and_item_comb_list_no_data_filter_usort_itemid_asc(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.USORT.value: filter_name.UrlSortName.ITEMID_ASC.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 8
    id = -1
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        assert id <= dic["item_id"]
        id = dic["item_id"]
        continue

    delete_item_model(test_db)


def test_get_url_and_item_comb_list_no_data_filter_usort_itemid_desc(test_db):
    add_data_set_1(test_db)
    filter_dict = {
        filter_name.FilterQueryName.USORT.value: filter_name.UrlSortName.ITEMID_DESC.id
    }
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 8
    id = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not id:
            id = dic["item_id"]
            continue
        assert id >= dic["item_id"]
        id = dic["item_id"]
        continue

    delete_item_model(test_db)


def test_get_url_and_item_comb_list_get_one_from_multiple_uniqname(test_db):
    add_data_set_2(test_db)
    filter_dict = {}
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 1
    res_dic: dict[int, int] = {}
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        url_id = int(dic["url_id"])
        if url_id in res_dic:
            assert url_id not in res_dic
        else:
            res_dic[url_id] = 1
            assert dic["uniqname"] == "one_item"
        continue
    delete_item_model(test_db)


def test_get_url_and_item_comb_list_get_a_non_blank_from_multiple_uniqname(test_db):
    add_data_set_3(test_db)
    filter_dict = {}
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 1
    res_dic: dict[int, int] = {}
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        url_id = int(dic["url_id"])
        if url_id in res_dic:
            assert url_id not in res_dic
        else:
            res_dic[url_id] = 1
            assert dic["uniqname"] == "one_other_item_name"
        continue
    delete_item_model(test_db)


def test_get_url_and_item_comb_list_get_a_blank_from_one_uniqname(test_db):
    add_data_set_4(test_db)
    filter_dict = {}
    results = UrlQuery.get_url_and_item_comb_list_in_local_time(
        test_db, filter=filter_dict
    )
    assert len(results) == 1
    res_dic: dict[int, int] = {}
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        url_id = int(dic["url_id"])
        if url_id in res_dic:
            assert url_id not in res_dic
        else:
            res_dic[url_id] = 1
            assert str(dic["uniqname"]).strip() == ""
        continue
    delete_item_model(test_db)


def test_get_storename_newest_data_no_data(test_db):
    store_id = 0
    filter_dict = {filter_name.FilterQueryName.EX_STORE.value: store_id}
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    assert len(results) == 0


def test_get_storename_newest_data_exist_data(test_db):
    add_data_set_1_plus_store(test_db)
    store_id = 1
    filter_dict = {filter_name.FilterQueryName.EX_STORE.value: store_id}
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    assert len(results) == 4
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {filter_name.FilterQueryName.EX_STORE.value: store_id}
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    assert len(results) == 5

    delete_item_and_store_model(test_db)


###############################
# ACT Filter
###############################


def test_get_storename_newest_data_exist_data_dup_filter_act(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.ACT.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    assert len(results) == 4

    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_inact(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.INACT.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    assert len(results) == 1

    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_all(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ACT.value: filter_name.ActFilterName.ALL.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    assert len(results) == 5

    delete_item_and_store_model(test_db)


###############################
# ExtractStoreSort Filter
###############################
def test_get_storename_newest_data_exist_data_dup_filter_essort_old_item(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ESSORT.value: filter_name.ExtractStoreSortName.OLD_ITEM.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    assert len(results) == 5
    old_id = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not old_id:
            old_id = int(dic["item_id"])
            continue
        if old_id:
            assert old_id <= int(dic["item_id"])
            old_id = int(dic["item_id"])
            continue
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_essort_new_item(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ESSORT.value: filter_name.ExtractStoreSortName.NEW_ITEM.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    assert len(results) == 5
    new_id = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not new_id:
            new_id = int(dic["item_id"])
            continue
        if new_id:
            assert new_id >= int(dic["item_id"])
            new_id = int(dic["item_id"])
            continue
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_essort_low_price(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ESSORT.value: filter_name.ExtractStoreSortName.LOW_PRICE.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    assert len(results) == 5
    price = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not price:
            price = int(dic["price"])
            continue
        if price:
            assert price <= int(dic["price"])
            price = int(dic["price"])
            continue
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_essort_high_price(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ESSORT.value: filter_name.ExtractStoreSortName.HIGH_PRICE.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    price = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not price:
            price = int(dic["price"])
            continue
        if price:
            assert price >= int(dic["price"])
            price = int(dic["price"])
            continue
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_essort_low_trendrate(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ESSORT.value: filter_name.ExtractStoreSortName.LOW_TRENDRATE.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    rate = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not rate:
            rate = float(dic["trendrate"])
            continue
        if rate:
            assert rate <= float(dic["trendrate"])
            rate = float(dic["trendrate"])
            continue
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_essort_high_trendrate(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ESSORT.value: filter_name.ExtractStoreSortName.HIGH_TRENDRATE.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    rate = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not rate:
            rate = float(dic["trendrate"])
            continue
        if rate:
            assert rate >= float(dic["trendrate"])
            rate = float(dic["trendrate"])
            continue
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_essort_old_updatetime(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ESSORT.value: filter_name.ExtractStoreSortName.OLD_UPDATE_TIME.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    uptime = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not uptime:
            uptime = dbtimeTodatetime(dic["created_at"])
            continue
        if uptime:
            assert uptime <= dbtimeTodatetime(dic["created_at"])
            uptime = dbtimeTodatetime(dic["created_at"])
            continue
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_essort_new_updatetime(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ESSORT.value: filter_name.ExtractStoreSortName.NEW_UPDATE_TIME.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    uptime = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not uptime:
            uptime = dbtimeTodatetime(dic["created_at"])
            continue
        if uptime:
            assert uptime >= dbtimeTodatetime(dic["created_at"])
            uptime = dbtimeTodatetime(dic["created_at"])
            continue
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_essort_low_lowest_price(
    test_db,
):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ESSORT.value: filter_name.ExtractStoreSortName.LOW_LOWESTPRICE.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)

    price = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not price:
            price = int(dic["lowestprice"])
            continue
        if price:
            assert price <= int(dic["lowestprice"])
            price = int(dic["lowestprice"])
            continue
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_essort_high_lowest_price(
    test_db,
):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ESSORT.value: filter_name.ExtractStoreSortName.HIGH_LOWESTPRICE.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)

    price = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not price:
            price = int(dic["lowestprice"])
            continue
        if price:
            assert price >= int(dic["lowestprice"])
            price = int(dic["lowestprice"])
            continue
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_essort_closest_lowest_price(
    test_db,
):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ESSORT.value: filter_name.ExtractStoreSortName.CLOSEST_LOWESTPRICE.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)

    def get_compare_val(dic: dict):
        return int(dic["price"]) - int(dic["lowestprice"])

    pre_diff = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not pre_diff:
            pre_diff = get_compare_val(dic)
            continue
        if pre_diff:
            assert pre_diff <= get_compare_val(dic)
            pre_diff = get_compare_val(dic)
            continue
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_dup_filter_essort_furthest_lowest_price(
    test_db,
):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ESSORT.value: filter_name.ExtractStoreSortName.FURTHEST_LOWESTPRICE.id,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)

    def get_compare_val(dic: dict):
        return int(dic["price"]) - int(dic["lowestprice"])

    pre_diff = None
    for res in results:
        dic = {k: y for k, y in res._mapping.items()}
        if not pre_diff:
            pre_diff = get_compare_val(dic)
            continue
        if pre_diff:
            assert pre_diff >= get_compare_val(dic)
            pre_diff = get_compare_val(dic)
            continue
    delete_item_and_store_model(test_db)


###############################
# ZAIKO Filter
###############################


def test_get_storename_newest_data_exist_data_filter_zaiko_on(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ZAIKO.value: filter_name.FilterOnOff.ON,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    assert len(results) == 4
    delete_item_and_store_model(test_db)


def test_get_storename_newest_data_exist_data_filter_zaiko_off(test_db):
    add_extract_store_data_set_1(test_db)
    store_id = 1
    filter_dict = {
        filter_name.FilterQueryName.EX_STORE.value: store_id,
        filter_name.FilterQueryName.ZAIKO.value: filter_name.FilterOnOff.OFF,
    }
    results = NewestQuery.get_storename_newest_data(test_db, filter=filter_dict)
    assert len(results) == 5
    delete_item_and_store_model(test_db)


###############################
# Delete URL
###############################


def test_delete_all_related_by_url(test_db):
    add_data_set_1(test_db)
    url_id = 1
    results = NewestQuery.get_raw_newest_data_all(test_db)
    check_item_id = None
    assert len(results) == 8
    for ni in results:
        if ni.url_id == url_id:
            check_item_id = int(ni.item_id)
            break
    assert check_item_id
    UrlQuery.delete_all_related_by_url(test_db, url_id=url_id)
    ret = UrlQuery.get_urlinitem(test_db, url_id=url_id, item_id=check_item_id)
    assert not ret
    results = ItemQuery.get_pricelog_2days_by_url_id(test_db, url_id=url_id)
    assert not results
    results = ItemQuery.get_pricelog_by_url_id(test_db, url_id=url_id)
    assert not results
    delete_item_model(test_db)


def test_update_by_deleting_url(test_db):
    add_data_set_1(test_db)
    url_id = 1
    results = NewestQuery.get_raw_newest_data_all(test_db)
    check_item_id = None
    assert len(results) == 8
    for ni in results:
        if ni.url_id == url_id:
            check_item_id = int(ni.item_id)
            break
    assert check_item_id

    NewestQuery.update_by_deleting_url(test_db, url_id=url_id)
    results = NewestQuery.get_raw_newest_data_all(test_db)
    assert len(results) == 8
    for ni in results:
        if ni.item_id == check_item_id:
            assert not ni.url_id
            assert ni.newestprice == const_value.INIT_PRICE
            assert not ni.salename
            assert str(ni.onsale) == "0"
            assert str(ni.taxin) == "0"
            assert int(ni.trendrate) == 0
            break
    delete_item_model(test_db)

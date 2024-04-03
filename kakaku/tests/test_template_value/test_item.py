from datetime import datetime, timezone

from common import filter_name, util
from parameter_parser import item as ppi
from template_value import item

from tests.data.stab_class import DBResult
from tests.test_db import test_db


def assert_created_at_asc(res):
    cur = None
    for r in res:
        if cur is None:
            cur = r.created_at
            continue
        assert cur <= r.created_at


def assert_created_at_desc(res):
    cur = None
    for r in res:
        if cur is None:
            cur = r.created_at
            continue
        assert cur >= r.created_at


def check_UrlListContext_sort_update_time_no_database_access(
    test_db, mocker, db_return: list[dict], assert_func, result_length: int
):
    results: list[DBResult] = []
    for r in db_return:
        results.append(DBResult(r))
    m = mocker.patch(
        "template_value.item.UrlQuery.get_url_and_item_comb_list_in_local_time",
        return_value=results,
    )
    usort = str(filter_name.UrlSortName.UPDATE_TIME_ASC.id)
    ufq = ppi.UrlListFilterQuery(usort=usort)
    ulc = item.UrlListContext(db=test_db, ufq=ufq)
    context = ulc.get_context()
    assert len(context["res"]) == result_length
    assert_func(res=context["res"])


def test_UrlListContext_sort_update_time_asc_no_database_access_01(test_db, mocker):
    date_format = "%Y-%m-%d %H:%M"
    db_return: list[dict] = [
        {
            "url_id": 1,
            "urlpath": "https://xxx",
            "uniqname": "one",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2024-01-01 00:00", date_format),
            "item_id": 1,
            "itemname": "one_item",
            "active": "1",
        },
        {
            "url_id": 2,
            "urlpath": "https://xxx",
            "uniqname": "two",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2024-01-02 00:00", date_format),
            "item_id": 2,
            "itemname": "two_item",
            "active": "1",
        },
        {
            "url_id": 3,
            "urlpath": "https://xxx",
            "uniqname": "three",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2024-01-03 00:00", date_format),
            "item_id": 3,
            "itemname": "three_item",
            "active": "1",
        },
    ]
    check_UrlListContext_sort_update_time_no_database_access(
        test_db=test_db,
        mocker=mocker,
        db_return=db_return,
        assert_func=assert_created_at_asc,
        result_length=3,
    )


def test_UrlListContext_sort_update_time_asc_no_database_access_02(test_db, mocker):
    date_format = "%Y-%m-%d %H:%M"
    db_return: list[dict] = [
        {
            "url_id": 1,
            "urlpath": "https://xxx",
            "uniqname": "one",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2024-01-01 00:00", date_format),
            "item_id": 1,
            "itemname": "one_item",
            "active": "1",
        },
        {
            "url_id": 2,
            "urlpath": "https://xxx",
            "uniqname": "two",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2024-01-02 00:00", date_format),
            "item_id": 2,
            "itemname": "two_item",
            "active": "1",
        },
        {
            "url_id": 1,
            "urlpath": "https://xxx",
            "uniqname": "three",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2024-01-03 00:00", date_format),
            "item_id": 3,
            "itemname": "three_item",
            "active": "1",
        },
    ]
    check_UrlListContext_sort_update_time_no_database_access(
        test_db=test_db,
        mocker=mocker,
        db_return=db_return,
        assert_func=assert_created_at_asc,
        result_length=2,
    )


def test_UrlListContext_sort_update_time_desc_no_database_access_01(test_db, mocker):
    date_format = "%Y-%m-%d %H:%M"
    db_return: list[dict] = [
        {
            "url_id": 3,
            "urlpath": "https://xxx",
            "uniqname": "three",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2024-01-03 00:00", date_format),
            "item_id": 3,
            "itemname": "three_item",
            "active": "1",
        },
        {
            "url_id": 2,
            "urlpath": "https://xxx",
            "uniqname": "two",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2024-01-02 00:00", date_format),
            "item_id": 2,
            "itemname": "two_item",
            "active": "1",
        },
        {
            "url_id": 1,
            "urlpath": "https://xxx",
            "uniqname": "one",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2024-01-01 00:00", date_format),
            "item_id": 1,
            "itemname": "one_item",
            "active": "1",
        },
    ]
    check_UrlListContext_sort_update_time_no_database_access(
        test_db=test_db,
        mocker=mocker,
        db_return=db_return,
        assert_func=assert_created_at_desc,
        result_length=3,
    )


def test_UrlListContext_sort_update_time_desc_no_database_access_02(test_db, mocker):
    date_format = "%Y-%m-%d %H:%M"
    db_return: list[dict] = [
        {
            "url_id": 3,
            "urlpath": "https://xxx",
            "uniqname": "three",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2024-01-03 00:00", date_format),
            "item_id": 3,
            "itemname": "three_item",
            "active": "1",
        },
        {
            "url_id": 2,
            "urlpath": "https://xxx",
            "uniqname": "two",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2024-01-02 00:00", date_format),
            "item_id": 2,
            "itemname": "two_item",
            "active": "1",
        },
        {
            "url_id": 1,
            "urlpath": "https://xxx",
            "uniqname": "one",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2024-01-01 00:00", date_format),
            "item_id": 1,
            "itemname": "one_item",
            "active": "1",
        },
        {
            "url_id": 3,
            "urlpath": "https://xxx",
            "uniqname": "one",
            "registration_date": datetime.strptime("2024-01-01 00:00", date_format),
            "created_at": datetime.strptime("2023-12-01 00:00", date_format),
            "item_id": 3,
            "itemname": "three_item",
            "active": "1",
        },
    ]
    check_UrlListContext_sort_update_time_no_database_access(
        test_db=test_db,
        mocker=mocker,
        db_return=db_return,
        assert_func=assert_created_at_desc,
        result_length=3,
    )


def test_CompressLogByStorename_no_list():
    loglist = []
    plog = item.CompressLogByStorename(loglist=loglist)
    assert len(plog.get_log_list()) == 0


def test_CompressLogByStorename_one_data():
    loglist = [
        {
            "url_id": 1,
            "storename": "A",
            "created_at": datetime(2024, 4, 3, hour=6, minute=0, second=0),
            "newprice": -1,
            "usedprice": 500,
        }
    ]
    plog = item.CompressLogByStorename(loglist=loglist)
    results = plog.get_log_list()
    assert len(results) == 1
    assert loglist == results


def test_CompressLogByStorename_three_data_sorted():
    loglist = [
        {
            "url_id": 1,
            "storename": "A",
            "created_at": datetime(2024, 4, 3, hour=6, minute=0, second=0),
            "newprice": -1,
            "usedprice": 500,
        },
        {
            "url_id": 2,
            "storename": "B",
            "created_at": datetime(2024, 4, 5, hour=6, minute=0, second=0),
            "newprice": -1,
            "usedprice": 700,
        },
        {
            "url_id": 3,
            "storename": "C",
            "created_at": datetime(2024, 4, 3, hour=10, minute=0, second=0),
            "newprice": -1,
            "usedprice": 400,
        },
    ]
    plog = item.CompressLogByStorename(loglist=loglist)
    results = plog.get_log_list()
    assert len(results) == 3
    assert sorted(loglist, key=lambda l: l["created_at"], reverse=True) == results


def test_CompressLogByStorename_five_data_compress_two():
    loglist = [
        {
            "url_id": 1,
            "storename": "A",
            "created_at": datetime(2024, 4, 3, hour=6, minute=0, second=0),
            "newprice": -1,
            "usedprice": 500,
        },
        {
            "url_id": 1,
            "storename": "A",
            "created_at": datetime(2024, 4, 4, hour=6, minute=0, second=0),
            "newprice": -1,
            "usedprice": 500,
        },
        {
            "url_id": 2,
            "storename": "B",
            "created_at": datetime(2024, 4, 5, hour=6, minute=0, second=0),
            "newprice": -1,
            "usedprice": 700,
        },
        {
            "url_id": 3,
            "storename": "C",
            "created_at": datetime(2024, 4, 3, hour=10, minute=0, second=0),
            "newprice": -1,
            "usedprice": 400,
        },
        {
            "url_id": 3,
            "storename": "C",
            "created_at": datetime(2024, 4, 6, hour=10, minute=0, second=0),
            "newprice": -1,
            "usedprice": 400,
        },
    ]
    plog = item.CompressLogByStorename(loglist=loglist)
    results = plog.get_log_list()
    assert len(results) == 3
    pre_data = None
    for r in results:
        if not pre_data:
            pre_data = r
            continue
        assert pre_data["created_at"] >= r["created_at"]


def test_CompressLogByStorename_four_data_comporess_four():
    loglist = [
        {
            "url_id": 1,
            "storename": "A",
            "created_at": datetime(2024, 4, 3, hour=6, minute=0, second=0),
            "newprice": -1,
            "usedprice": 500,
        },
        {
            "url_id": 1,
            "storename": "A",
            "created_at": datetime(2024, 4, 5, hour=6, minute=0, second=0),
            "newprice": -1,
            "usedprice": 500,
        },
        {
            "url_id": 1,
            "storename": "A",
            "created_at": datetime(2024, 4, 3, hour=10, minute=0, second=0),
            "newprice": -1,
            "usedprice": 500,
        },
        {
            "url_id": 1,
            "storename": "A",
            "created_at": datetime(2024, 5, 28, hour=10, minute=0, second=0),
            "newprice": -1,
            "usedprice": 500,
        },
    ]
    plog = item.CompressLogByStorename(loglist=loglist)
    results = plog.get_log_list()
    assert len(results) == 1
    assert results[0]["created_at"] == loglist[3]["created_at"]


def test_CompressLogByStorename_three_data_no_comporess():
    loglist = [
        {
            "url_id": 1,
            "storename": "A",
            "created_at": datetime(2024, 4, 3, hour=6, minute=0, second=0),
            "newprice": -1,
            "usedprice": 500,
        },
        {
            "url_id": 1,
            "storename": "A",
            "created_at": datetime(2024, 4, 5, hour=6, minute=0, second=0),
            "newprice": -1,
            "usedprice": 700,
        },
        {
            "url_id": 1,
            "storename": "A",
            "created_at": datetime(2024, 4, 3, hour=10, minute=0, second=0),
            "newprice": -1,
            "usedprice": 400,
        },
    ]
    plog = item.CompressLogByStorename(loglist=loglist)
    results = plog.get_log_list()
    assert len(results) == 3
    assert sorted(loglist, key=lambda l: l["created_at"], reverse=True) == results

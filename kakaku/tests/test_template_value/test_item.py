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

from datetime import datetime, timedelta, timezone

from common.util import dbtimeTodatetime
from tests.test_sqlalchemy import (
    insert_item_dict_list,
    insert_url_dict_list,
    insert_pricelog_dict_list_sync,
    insert_urlinitem_dict_list,
)

SURUGAYA = "駿河屋"


def add_price_range_1(db):
    pricelog_list = [
        {
            "url_id": 1,
            "created_at": dbtimeTodatetime("2024-01-01 10:00:00"),
            "uniqname": "one_item_1",
            "usedprice": 1500,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": SURUGAYA,
        },
        {
            "url_id": 1,
            "created_at": dbtimeTodatetime("2024-01-05 10:00:00"),
            "uniqname": "one_item_1",
            "usedprice": 1200,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": SURUGAYA,
        },
        {
            "url_id": 1,
            "created_at": dbtimeTodatetime("2024-02-01 10:00:00"),
            "uniqname": "one_item_1",
            "usedprice": 1200,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": SURUGAYA,
        },
        {
            "url_id": 1,
            "created_at": dbtimeTodatetime("2024-03-14 10:00:00"),
            "uniqname": "one_item_1",
            "usedprice": 1600,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": SURUGAYA,
        },
    ]
    insert_pricelog_dict_list_sync(db, pldict_list=pricelog_list)


def add_item_url_pricelog_1(db):
    item_list = [
        {"item_id": 1, "name": "one_item"},
        {"item_id": 2, "name": "two_item"},
    ]
    url_list = [
        {"url_id": 1, "urlpath": SURUGAYA},
        {"url_id": 2, "urlpath": SURUGAYA},
        {"url_id": 3, "urlpath": SURUGAYA},
        {"url_id": 4, "urlpath": SURUGAYA},
    ]
    urlinitem_list = [
        {"item_id": 1, "url_id": 1, "active": "True"},
        {"item_id": 1, "url_id": 2, "active": "True"},
        {"item_id": 2, "url_id": 3, "active": "True"},
        {"item_id": 2, "url_id": 4, "active": "False"},
    ]
    pricelog_list = [
        {
            "url_id": 1,
            "created_at": dbtimeTodatetime("2024-01-01 10:00:00"),
            "uniqname": "one_item_1",
            "usedprice": 1500,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": SURUGAYA,
        },
        {
            "url_id": 2,
            "created_at": dbtimeTodatetime("2024-01-01 10:01:00"),
            "uniqname": "one_item_2",
            "usedprice": 1200,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0.177,
            "storename": SURUGAYA,
        },
        {
            "url_id": 3,
            "created_at": dbtimeTodatetime("2024-01-01 10:02:00"),
            "uniqname": "two_item_1",
            "usedprice": 3000,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": -0.07,
            "storename": SURUGAYA,
        },
        {
            "url_id": 4,
            "created_at": dbtimeTodatetime("2024-01-01 10:03:00"),
            "uniqname": "two_item_2",
            "usedprice": 3300,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": SURUGAYA,
        },
    ]

    insert_item_dict_list(db, item_list=item_list)
    insert_url_dict_list(db, url_list=url_list)
    insert_urlinitem_dict_list(db, urlinitem_list=urlinitem_list)
    insert_pricelog_dict_list_sync(db, pldict_list=pricelog_list)

from datetime import datetime, timedelta, timezone

from common.util import dbtimeTodatetime
from tests.test_sqlalchemy import (
    insert_item_dict_list,
    insert_url_dict_list,
    insert_newestitem_dict_list,
    insert_pricelog_dict_list_sync,
    insert_urlinitem_dict_list,
    insert_store_dict_list,
    insert_store_postage_dict_list,
    insert_online_store_dict_list,
    insert_online_store_postage_dict_list,
    insert_daily_online_shop_info_dict_list,
)

SURUGAYA_OTHER_GEDOSENKI = "https://www.suruga-ya.jp/product-other/128022745"
SURUGAYA_OTHER_RAPYUTA = "https://www.suruga-ya.jp/product-other/128006258"
SURUGAYA_OTHER_MONONOKE = "https://www.suruga-ya.jp/product-other/128049960"
SURUGAYA_PRODUCT_MIMIWO = "https://www.suruga-ya.jp/product/detail/128004530"
SURUGAYA_OTHER_KOKURIKO = "https://www.suruga-ya.jp/product-other/428003178"
SURUGAYA_OTHER_HAURU = "https://www.suruga-ya.jp/product-other/128016917"
NETOFF_HAURU = "https://www.netoff.co.jp/detail/0010173144"
BOOKOFF_SENTOCHIHIRO = "https://www.bookoffonline.co.jp/old/0001243579"
SURUGAYA_PONYO = "https://www.suruga-ya.jp/product/detail/128030031"

SURUGAYA = "駿河屋"
SURUGAYA_CHIBA = "駿河屋千葉中央店"
NETOFF = "ネットオフ"
BOOKOFF = "ブックオフ"


def add_data_set_1(db):
    item_list = [
        {"item_id": 1, "name": "one_item"},
        {"item_id": 2, "name": "two_item"},
        {"item_id": 3, "name": "three_item"},
        {"item_id": 4, "name": "four_item"},
        {"item_id": 5, "name": "five_item"},
        {"item_id": 6, "name": "six_item"},
        {"item_id": 7, "name": "seven_item"},
        {"item_id": 8, "name": "eight_item"},
    ]
    url_list = [
        {"url_id": 1, "urlpath": SURUGAYA_OTHER_GEDOSENKI},
        {"url_id": 2, "urlpath": SURUGAYA_OTHER_RAPYUTA},
        {"url_id": 3, "urlpath": SURUGAYA_OTHER_MONONOKE},
        {"url_id": 4, "urlpath": SURUGAYA_PRODUCT_MIMIWO},
        {"url_id": 5, "urlpath": SURUGAYA_OTHER_KOKURIKO},
        {"url_id": 6, "urlpath": NETOFF_HAURU},
        {"url_id": 7, "urlpath": BOOKOFF_SENTOCHIHIRO},
        {"url_id": 8, "urlpath": SURUGAYA_PONYO},
    ]
    urlinitem_list = [
        {"item_id": 1, "url_id": 1, "active": "True"},
        {"item_id": 2, "url_id": 2, "active": "True"},
        {"item_id": 3, "url_id": 3, "active": "True"},
        {"item_id": 4, "url_id": 4, "active": "False"},
        {"item_id": 5, "url_id": 5, "active": "True"},
        {"item_id": 6, "url_id": 6, "active": "True"},
        {"item_id": 7, "url_id": 7, "active": "True"},
        {"item_id": 8, "url_id": 8, "active": "True"},
    ]
    pricelog_list = [
        {
            "url_id": 1,
            "created_at": dbtimeTodatetime("2023-08-22 10:00:00"),
            "uniqname": "one_item",
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
            "created_at": dbtimeTodatetime("2023-08-22 10:01:00"),
            "uniqname": "two_item",
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
            "created_at": dbtimeTodatetime("2023-08-22 10:02:00"),
            "uniqname": "three_item",
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
            "created_at": dbtimeTodatetime("2023-08-21 10:03:00"),
            "uniqname": "four_item",
            "usedprice": 3300,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": SURUGAYA,
        },
        {
            "url_id": 5,
            "created_at": dbtimeTodatetime("2023-08-22 10:04:00"),
            "uniqname": "five_item",
            "usedprice": -1,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": SURUGAYA,
        },
        {
            "url_id": 6,
            "created_at": dbtimeTodatetime("2023-08-22 10:05:00"),
            "uniqname": "six_item",
            "usedprice": 1400,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0.03,
            "storename": NETOFF,
        },
        {
            "url_id": 7,
            "created_at": dbtimeTodatetime("2023-08-22 10:06:00"),
            "uniqname": "seven_item",
            "usedprice": 1700,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": -0.19,
            "storename": BOOKOFF,
        },
        {
            "url_id": 8,
            "created_at": dbtimeTodatetime("2023-08-22 10:07:00"),
            "uniqname": "eight_item",
            "usedprice": 3380,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": SURUGAYA,
        },
    ]
    newestitem_list = [
        {
            "item_id": 1,
            "url_id": 1,
            "created_at": dbtimeTodatetime("2023-08-22 10:00:00"),
            "newestprice": 1500,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "trendrate": 0,
            "storename": SURUGAYA,
            "lowestprice": 1500,
        },
        {
            "item_id": 2,
            "url_id": 2,
            "created_at": dbtimeTodatetime("2023-08-22 10:01:00"),
            "newestprice": 1200,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "trendrate": 0.177,
            "storename": SURUGAYA,
            "lowestprice": 1000,
        },
        {
            "item_id": 3,
            "url_id": 3,
            "created_at": dbtimeTodatetime("2023-08-22 10:02:00"),
            "newestprice": 3000,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "trendrate": -0.07,
            "storename": SURUGAYA,
            "lowestprice": 2800,
        },
        {
            "item_id": 4,
            "url_id": 4,
            "created_at": dbtimeTodatetime("2023-08-21 10:03:00"),
            "newestprice": 3300,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "trendrate": 0.0,
            "storename": SURUGAYA,
            "lowestprice": 2800,
        },
        {
            "item_id": 5,
            "url_id": 5,
            "created_at": dbtimeTodatetime("2023-08-22 10:04:00"),
            "newestprice": -1,
            "taxin": False,
            "onsale": False,
            "salename": None,
            "trendrate": 0.0,
            "storename": SURUGAYA,
            "lowestprice": 2980,
        },
        {
            "item_id": 6,
            "url_id": 6,
            "created_at": dbtimeTodatetime("2023-08-22 10:05:00"),
            "newestprice": 1400,
            "taxin": False,
            "onsale": False,
            "salename": None,
            "trendrate": 0.03,
            "storename": NETOFF,
            "lowestprice": 1300,
        },
        {
            "item_id": 7,
            "url_id": 7,
            "created_at": dbtimeTodatetime("2023-08-22 10:06:00"),
            "newestprice": 1700,
            "taxin": False,
            "onsale": False,
            "salename": None,
            "trendrate": -0.19,
            "storename": BOOKOFF,
            "lowestprice": 1700,
        },
        {
            "item_id": 8,
            "url_id": 8,
            "created_at": dbtimeTodatetime("2023-08-22 10:07:00"),
            "newestprice": 3380,
            "taxin": False,
            "onsale": False,
            "salename": None,
            "trendrate": 0,
            "storename": SURUGAYA,
            "lowestprice": 1900,
        },
    ]
    insert_item_dict_list(db, item_list=item_list)
    insert_url_dict_list(db, url_list=url_list)
    insert_urlinitem_dict_list(db, urlinitem_list=urlinitem_list)
    insert_pricelog_dict_list_sync(db, pldict_list=pricelog_list)
    insert_newestitem_dict_list(db, nidict_list=newestitem_list)


def add_data_set_1_plus_store(db):
    add_data_set_1(db)
    add_data_store(db)


def add_data_of_multiple_uniqname_one_item(db):
    item_list = [
        {"item_id": 1, "name": "one_item"},
    ]
    url_list = [
        {"url_id": 1, "urlpath": SURUGAYA_OTHER_GEDOSENKI},
    ]
    urlinitem_list = [
        {"item_id": 1, "url_id": 1, "active": "True"},
    ]
    insert_item_dict_list(db, item_list=item_list)
    insert_url_dict_list(db, url_list=url_list)
    insert_urlinitem_dict_list(db, urlinitem_list=urlinitem_list)


def add_data_set_2(db):
    add_data_of_multiple_uniqname_one_item(db)
    pricelog_list = [
        {
            "url_id": 1,
            "created_at": dbtimeTodatetime("2023-08-22 10:00:00"),
            "uniqname": "one_item",
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
            "created_at": dbtimeTodatetime("2023-08-21 10:01:00"),
            "uniqname": "other",
            "usedprice": 1200,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0.177,
            "storename": SURUGAYA,
        },
    ]
    insert_pricelog_dict_list_sync(db, pldict_list=pricelog_list)


def add_data_set_3(db):
    add_data_of_multiple_uniqname_one_item(db)
    pricelog_list = [
        {
            "url_id": 1,
            "created_at": dbtimeTodatetime("2023-08-22 10:00:00"),
            "uniqname": "  ",
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
            "created_at": dbtimeTodatetime("2023-08-21 10:01:00"),
            "uniqname": "one_other_item_name",
            "usedprice": 1200,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0.177,
            "storename": SURUGAYA,
        },
    ]
    insert_pricelog_dict_list_sync(db, pldict_list=pricelog_list)


def add_data_set_4(db):
    add_data_of_multiple_uniqname_one_item(db)
    pricelog_list = [
        {
            "url_id": 1,
            "created_at": dbtimeTodatetime("2023-08-22 10:00:00"),
            "uniqname": "  ",
            "usedprice": 1500,
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


def add_data_store(db):
    storename_list = [
        {"store_id": 1, "storename": SURUGAYA},
        {"store_id": 2, "storename": NETOFF},
        {"store_id": 3, "storename": BOOKOFF},
        {"store_id": 4, "storename": SURUGAYA},
    ]
    insert_store_dict_list(db, storename_dict_list=storename_list)


def add_data_store_postage(db):
    store_pos_list = [
        {"store_id": 1, "terms_id": 1, "boundary": "1000>", "postage": 500},
        {"store_id": 1, "terms_id": 2, "boundary": "1500>:1000<=", "postage": 440},
        {"store_id": 2, "terms_id": 1, "boundary": "1500>", "postage": 440},
        {"store_id": 4, "terms_id": 1, "boundary": "2000>", "postage": 600},
    ]
    insert_store_postage_dict_list(db, store_pos_dict_list=store_pos_list)


def add_analysis_data_set_1(db):
    item_list = [
        {"item_id": 1, "name": "one_item"},
        {"item_id": 2, "name": "two_item"},
        {"item_id": 3, "name": "three_item"},
    ]
    url_list = [
        {"url_id": 1, "urlpath": SURUGAYA_OTHER_GEDOSENKI},
        {"url_id": 2, "urlpath": SURUGAYA_OTHER_RAPYUTA},
        {"url_id": 3, "urlpath": NETOFF_HAURU},
        {"url_id": 4, "urlpath": BOOKOFF_SENTOCHIHIRO},
    ]
    urlinitem_list = [
        {"item_id": 1, "url_id": 1, "active": "True"},
        {"item_id": 2, "url_id": 2, "active": "True"},
        {"item_id": 3, "url_id": 3, "active": "True"},
        {"item_id": 3, "url_id": 4, "active": "True"},
    ]
    one_week_ago = datetime.now(timezone.utc) + timedelta(days=-7)
    three_days_ago = datetime.now(timezone.utc) + timedelta(days=-3)

    pricelog_list = [
        {
            "url_id": 1,
            "created_at": one_week_ago,
            "uniqname": "one_item",
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
            "created_at": one_week_ago,
            "uniqname": "two_item",
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
            "url_id": 2,
            "created_at": one_week_ago,
            "uniqname": "two_item2",
            "usedprice": 1600,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": SURUGAYA_CHIBA,
        },
        {
            "url_id": 3,
            "created_at": one_week_ago,
            "uniqname": "three_item",
            "usedprice": 3000,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": NETOFF_HAURU,
        },
        {
            "url_id": 4,
            "created_at": one_week_ago,
            "uniqname": "four_item",
            "usedprice": 3300,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": BOOKOFF_SENTOCHIHIRO,
        },
        {
            "url_id": 1,
            "created_at": three_days_ago,
            "uniqname": "one_item",
            "usedprice": 1400,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": -0.07,
            "storename": SURUGAYA,
        },
        {
            "url_id": 2,
            "created_at": three_days_ago,
            "uniqname": "two_item",
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
            "url_id": 2,
            "created_at": three_days_ago,
            "uniqname": "two_item2",
            "usedprice": 1600,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0.33,
            "storename": SURUGAYA_CHIBA,
        },
        {
            "url_id": 3,
            "created_at": three_days_ago,
            "uniqname": "three_item",
            "usedprice": 3000,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": NETOFF_HAURU,
        },
        {
            "url_id": 4,
            "created_at": three_days_ago,
            "uniqname": "four_item",
            "usedprice": 3300,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": BOOKOFF_SENTOCHIHIRO,
        },
        {
            "url_id": 1,
            "created_at": datetime.now(timezone.utc),
            "uniqname": "one_item",
            "usedprice": 1400,
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
            "created_at": datetime.now(timezone.utc),
            "uniqname": "two_item",
            "usedprice": 1000,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": -0.17,
            "storename": SURUGAYA,
        },
        {
            "url_id": 2,
            "created_at": datetime.now(timezone.utc),
            "uniqname": "two_item2",
            "usedprice": 1600,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0.6,
            "storename": SURUGAYA_CHIBA,
        },
        {
            "url_id": 3,
            "created_at": datetime.now(timezone.utc),
            "uniqname": "three_item",
            "usedprice": 3300,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0.1,
            "storename": NETOFF_HAURU,
        },
        {
            "url_id": 4,
            "created_at": datetime.now(timezone.utc),
            "uniqname": "four_item",
            "usedprice": 3600,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0.09,
            "storename": BOOKOFF_SENTOCHIHIRO,
        },
    ]

    insert_item_dict_list(db, item_list=item_list)
    insert_url_dict_list(db, url_list=url_list)
    insert_urlinitem_dict_list(db, urlinitem_list=urlinitem_list)
    insert_pricelog_dict_list_sync(db, pldict_list=pricelog_list)


def add_extract_store_data_set_1(db):
    item_list = [
        {"item_id": 1, "name": "one_item"},
        {"item_id": 2, "name": "two_item"},
        {"item_id": 3, "name": "three_item"},
    ]
    url_list = [
        {"url_id": 1, "urlpath": SURUGAYA_OTHER_GEDOSENKI},
        {"url_id": 2, "urlpath": SURUGAYA_OTHER_RAPYUTA},
        {"url_id": 3, "urlpath": NETOFF_HAURU},
        {"url_id": 4, "urlpath": BOOKOFF_SENTOCHIHIRO},
        {"url_id": 5, "urlpath": SURUGAYA_OTHER_KOKURIKO},
    ]
    urlinitem_list = [
        {"item_id": 1, "url_id": 1, "active": "True"},
        {"item_id": 1, "url_id": 2, "active": "True"},
        {"item_id": 2, "url_id": 3, "active": "False"},
        {"item_id": 2, "url_id": 4, "active": "True"},
        {"item_id": 3, "url_id": 5, "active": "False"},
    ]
    pricelog_list = [
        {
            "url_id": 1,
            "created_at": dbtimeTodatetime("2023-08-22 10:00:00"),
            "uniqname": "one_item",
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
            "created_at": dbtimeTodatetime("2023-08-22 10:01:00"),
            "uniqname": "two_item",
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
            "created_at": dbtimeTodatetime("2023-08-22 10:02:00"),
            "uniqname": "three_item",
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
            "created_at": dbtimeTodatetime("2023-08-22 10:03:00"),
            "uniqname": "four_item",
            "usedprice": 3300,
            "newprice": 3400,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": SURUGAYA,
        },
        {
            "url_id": 5,
            "created_at": dbtimeTodatetime("2023-08-22 10:04:00"),
            "uniqname": "five_item",
            "usedprice": -1,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": SURUGAYA,
        },
    ]
    newestitem_list = [
        {
            "item_id": 1,
            "url_id": 1,
            "created_at": dbtimeTodatetime("2023-08-22 10:00:00"),
            "newestprice": 1500,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "trendrate": 0,
            "storename": SURUGAYA,
            "lowestprice": 1500,
        },
        {
            "item_id": 2,
            "url_id": 3,
            "created_at": dbtimeTodatetime("2023-08-22 10:01:00"),
            "newestprice": 1200,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "trendrate": 0.177,
            "storename": SURUGAYA,
            "lowestprice": 1000,
        },
        {
            "item_id": 3,
            "url_id": 5,
            "created_at": dbtimeTodatetime("2023-08-22 10:02:00"),
            "newestprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "trendrate": 0.0,
            "storename": SURUGAYA,
            "lowestprice": 2800,
        },
    ]
    insert_item_dict_list(db, item_list=item_list)
    insert_url_dict_list(db, url_list=url_list)
    insert_urlinitem_dict_list(db, urlinitem_list=urlinitem_list)
    insert_pricelog_dict_list_sync(db, pldict_list=pricelog_list)
    insert_newestitem_dict_list(db, nidict_list=newestitem_list)
    add_data_store(db)


def add_data_online_store(db):
    store_list = [
        {"shop_id": 1, "storename": SURUGAYA},
        {"shop_id": 2, "storename": SURUGAYA_CHIBA},
        {"shop_id": 3, "storename": NETOFF},
        {"shop_id": 4, "storename": BOOKOFF},
        {"shop_id": 5, "storename": SURUGAYA},
    ]
    insert_online_store_dict_list(db, store_dict_list=store_list)


def add_data_online_store_postage(db):
    store_pos_list = [
        {
            "shop_id": 1,
            "pref_id": 1,
            "terms_id": 1,
            "boundary": "1000>",
            "postage": 500,
            "campaign_msg": "",
            "insert_proc_type": 1,
        },
        {
            "shop_id": 1,
            "pref_id": 1,
            "terms_id": 2,
            "boundary": "1500>:1000<=",
            "postage": 440,
            "campaign_msg": "",
            "insert_proc_type": 1,
        },
        {
            "shop_id": 2,
            "pref_id": 1,
            "terms_id": 1,
            "boundary": "1500>",
            "postage": 480,
            "campaign_msg": "",
            "insert_proc_type": 1,
        },
        {
            "shop_id": 3,
            "pref_id": 1,
            "terms_id": 1,
            "boundary": "1500>",
            "postage": 440,
            "campaign_msg": "",
            "insert_proc_type": 1,
        },
        {
            "shop_id": 5,
            "pref_id": 1,
            "terms_id": 1,
            "boundary": "2000>",
            "postage": 600,
            "campaign_msg": "",
            "insert_proc_type": 1,
        },
    ]
    insert_online_store_postage_dict_list(db, store_pos_dict_list=store_pos_list)


def add_online_store_data_set_of_pricelog(db):
    now = datetime.now(timezone.utc)
    pricelog_list = [
        {
            "url_id": 1,
            "created_at": now,
            "uniqname": "one_item",
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
            "created_at": now,
            "uniqname": "two_item",
            "usedprice": 1200,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0.177,
            "storename": SURUGAYA_CHIBA,
        },
        {
            "url_id": 3,
            "created_at": dbtimeTodatetime("2023-08-22 10:03:00"),
            "uniqname": "three_item",
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
            "created_at": now,
            "uniqname": "four_item",
            "usedprice": 3300,
            "newprice": 3400,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": NETOFF,
        },
        {
            "url_id": 5,
            "created_at": dbtimeTodatetime("2023-08-22 10:04:00"),
            "uniqname": "five_item",
            "usedprice": -1,
            "newprice": -1,
            "taxin": True,
            "onsale": False,
            "salename": None,
            "issuccess": True,
            "trendrate": 0,
            "storename": BOOKOFF,
        },
    ]
    insert_pricelog_dict_list_sync(db, pldict_list=pricelog_list)


def add_online_store_data_set_1(db):
    add_data_online_store(db)
    add_data_online_store_postage(db)


def add_data_daily_online_shop_info(db):
    shop_info_list = [
        {
            "shop_id": 200910,
            "shop_name": "小山店",
            "url": "https://www.suruga-ya.jp/shop/200910",
            "insert_proc_type": 2,
        },
        {
            "shop_id": 400407,
            "shop_name": "千葉中央店",
            "url": "https://www.suruga-ya.jp/shop/400407",
            "insert_proc_type": 2,
        },
        {
            "shop_id": 400395,
            "shop_name": "ブックエコ浅川店",
            "url": "https://www.suruga-ya.jp/shop/400395",
            "insert_proc_type": 1,
        },
    ]
    insert_daily_online_shop_info_dict_list(db, shop_info_dict_list=shop_info_list)


def add_daily_online_shop_data_set_1(db):
    add_data_daily_online_shop_info(db)


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
            "usedprice": 1250,
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
            "created_at": dbtimeTodatetime("2024-03-14 10:00:01"),
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

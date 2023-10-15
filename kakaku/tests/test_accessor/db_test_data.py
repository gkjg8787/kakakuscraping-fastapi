
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from common.util import dbtimeTodatetime
from tests.test_sqlalchemy import (
    insert_item_dict_list,
    insert_url_dict_list,
    insert_newestitem_dict_list,
    insert_pricelog_dict_list_sync,
    insert_urlinitem_dict_list,
    insert_store_dict_list,
)

SURUGAYA_OTHER_GEDOSENKI = "https://www.suruga-ya.jp/product-other/128022745"
SURUGAYA_OTHER_RAPYUTA = "https://www.suruga-ya.jp/product-other/128006258"
SURUGAYA_OTHER_MONONOKE = "https://www.suruga-ya.jp/product-other/128049960"
SURUGAYA_PRODUCT_MIMIWO = "https://www.suruga-ya.jp/product/detail/128004530"
SURUGAYA_OTHER_KOKURIKO = "https://www.suruga-ya.jp/product-other/428003178"
SURUGAYA_OTHER_HAURU = "https://www.suruga-ya.jp/product-other/128016917"
NETOFF_HAURU = "https://www.netoff.co.jp/detail/0010173144"
BOOKOFF_SENTOCHIHIRO = "https://www.bookoffonline.co.jp/old/0001243579"
GEO_PONYO = "https://ec.geo-online.co.jp/shop/g/g192218002/"

SURUGAYA = "駿河屋"
SURUGAYA_CHIBA = "駿河屋千葉中央店"
NETOFF = "ネットオフ"
BOOKOFF = "ブックオフ"
GEO = "ゲオ"

def add_data_set_1(db):
    item_list = [
        {"item_id":1, "name":"one_item"},
        {"item_id":2, "name":"two_item"},
        {"item_id":3, "name":"three_item"},
        {"item_id":4, "name":"four_item"},
        {"item_id":5, "name":"five_item"},
        {"item_id":6, "name":"six_item"},
        {"item_id":7, "name":"seven_item"},
        {"item_id":8, "name":"eight_item"},
    ]
    url_list = [
        {"url_id":1, "urlpath":SURUGAYA_OTHER_GEDOSENKI},
        {"url_id":2, "urlpath":SURUGAYA_OTHER_RAPYUTA},
        {"url_id":3, "urlpath":SURUGAYA_OTHER_MONONOKE},
        {"url_id":4, "urlpath":SURUGAYA_PRODUCT_MIMIWO},
        {"url_id":5, "urlpath":SURUGAYA_OTHER_KOKURIKO},
        {"url_id":6, "urlpath":NETOFF_HAURU},
        {"url_id":7, "urlpath":BOOKOFF_SENTOCHIHIRO},
        {"url_id":8, "urlpath":GEO_PONYO},
    ]
    urlinitem_list = [
        {"item_id":1, "url_id":1, "active":"True"},
        {"item_id":2, "url_id":2, "active":"True"},
        {"item_id":3, "url_id":3, "active":"True"},
        {"item_id":4, "url_id":4, "active":"False"},
        {"item_id":5, "url_id":5, "active":"True"},
        {"item_id":6, "url_id":6, "active":"True"},
        {"item_id":7, "url_id":7, "active":"True"},
        {"item_id":8, "url_id":8, "active":"True"},
    ]
    pricelog_list = [
        {
            "url_id": 1, "created_at":dbtimeTodatetime("2023-08-22 10:00:00"),
            "uniqname":"one_item", "usedprice":1500, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":SURUGAYA,
        },
        {
            "url_id": 2, "created_at":dbtimeTodatetime("2023-08-22 10:01:00"),
            "uniqname":"two_item", "usedprice":1200, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0.177, "storename":SURUGAYA,
        },
        {
            "url_id": 3, "created_at":dbtimeTodatetime("2023-08-22 10:02:00"),
            "uniqname":"three_item", "usedprice":3000, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":-0.07, "storename":SURUGAYA,
        },
        {
            "url_id": 4, "created_at":dbtimeTodatetime("2023-08-21 10:03:00"),
            "uniqname":"four_item", "usedprice":3300, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":SURUGAYA,
        },
        {
            "url_id": 5, "created_at":dbtimeTodatetime("2023-08-22 10:04:00"),
            "uniqname":"five_item", "usedprice":-1, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":SURUGAYA,
        },
        {
            "url_id": 6, "created_at":dbtimeTodatetime("2023-08-22 10:05:00"),
            "uniqname":"six_item", "usedprice":1400, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0.03, "storename":NETOFF,
        },
        {
            "url_id": 7, "created_at":dbtimeTodatetime("2023-08-22 10:06:00"),
            "uniqname":"seven_item", "usedprice":1700, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":-0.19, "storename":BOOKOFF,
        },
        {
            "url_id": 8, "created_at":dbtimeTodatetime("2023-08-22 10:07:00"),
            "uniqname":"eight_item", "usedprice":3380, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":GEO,
        },
    ]
    newestitem_list = [
        {
            "item_id":1, "url_id": 1, "created_at":dbtimeTodatetime("2023-08-22 10:00:00"),
            "newestprice":1500,
            "taxin":True, "onsale":False, "salename":None,
            "trendrate":0, "storename":SURUGAYA,
            "lowestprice":1500,
        },
        {
            "item_id":2, "url_id": 2, "created_at":dbtimeTodatetime("2023-08-22 10:01:00"),
            "newestprice":1200,
            "taxin":True, "onsale":False, "salename":None,
            "trendrate":0.177, "storename":SURUGAYA,
            "lowestprice":1000,
        },
        {
            "item_id":3, "url_id": 3, "created_at":dbtimeTodatetime("2023-08-22 10:02:00"),
            "newestprice":3000,
            "taxin":True, "onsale":False, "salename":None,
            "trendrate":-0.07, "storename":SURUGAYA,
            "lowestprice":2800,
        },
        {
            "item_id":4, "url_id": 4, "created_at":dbtimeTodatetime("2023-08-21 10:03:00"),
            "newestprice":3300,
            "taxin":True, "onsale":False, "salename":None,
            "trendrate":0.0, "storename":SURUGAYA,
            "lowestprice":2800,
        },
        {
            "item_id":5, "url_id": 5, "created_at":dbtimeTodatetime("2023-08-22 10:04:00"),
            "newestprice":-1,
            "taxin":False, "onsale":False, "salename":None,
            "trendrate":0.0, "storename":SURUGAYA,
            "lowestprice":2980,
        },
        {
            "item_id":6, "url_id": 6, "created_at":dbtimeTodatetime("2023-08-22 10:05:00"),
            "newestprice":1400,
            "taxin":False, "onsale":False, "salename":None,
            "trendrate":0.03, "storename":NETOFF,
            "lowestprice":1300,
        },
        {
            "item_id":7, "url_id": 7, "created_at":dbtimeTodatetime("2023-08-22 10:06:00"),
            "newestprice":1700,
            "taxin":False, "onsale":False, "salename":None,
            "trendrate":-0.19, "storename":BOOKOFF,
            "lowestprice":1700,
        },
        {
            "item_id":8, "url_id": 8, "created_at":dbtimeTodatetime("2023-08-22 10:07:00"),
            "newestprice":3380,
            "taxin":False, "onsale":False, "salename":None,
            "trendrate":0, "storename":GEO,
            "lowestprice":1900,
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

def add_data_store(db):
    storename_list = [
        {"store_id":1, "storename":SURUGAYA},
        {"store_id":2, "storename":NETOFF},
        {"store_id":3, "storename":BOOKOFF},
        {"store_id":4, "storename":GEO},
    ]
    insert_store_dict_list(db, storename_dict_list=storename_list)

def add_analysis_data_set_1(db):
    item_list = [
        {"item_id":1, "name":"one_item"},
        {"item_id":2, "name":"two_item"},
        {"item_id":3, "name":"three_item"},
    ]
    url_list = [
        {"url_id":1, "urlpath":SURUGAYA_OTHER_GEDOSENKI},
        {"url_id":2, "urlpath":SURUGAYA_OTHER_RAPYUTA},
        {"url_id":3, "urlpath":NETOFF_HAURU},
        {"url_id":4, "urlpath":BOOKOFF_SENTOCHIHIRO},
    ]
    urlinitem_list = [
        {"item_id":1, "url_id":1, "active":"True"},
        {"item_id":2, "url_id":2, "active":"True"},
        {"item_id":3, "url_id":3, "active":"True"},
        {"item_id":3, "url_id":4, "active":"True"},
    ]
    one_week_ago = datetime.utcnow() + timedelta(days=-7)
    three_days_ago = datetime.utcnow() + timedelta(days=-3)

    pricelog_list = [
        {
            "url_id": 1, "created_at":one_week_ago,
            "uniqname":"one_item", "usedprice":1500, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":SURUGAYA,
        },
        {
            "url_id": 2, "created_at":one_week_ago,
            "uniqname":"two_item", "usedprice":1200, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":SURUGAYA,
        },
        {
            "url_id": 2, "created_at":one_week_ago,
            "uniqname":"two_item2", "usedprice":1600, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":SURUGAYA_CHIBA,
        },
        {
            "url_id": 3, "created_at":one_week_ago,
            "uniqname":"three_item", "usedprice":3000, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":NETOFF_HAURU,
        },
        {
            "url_id": 4, "created_at":one_week_ago,
            "uniqname":"four_item", "usedprice":3300, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":BOOKOFF_SENTOCHIHIRO,
        },
        {
            "url_id": 1, "created_at":three_days_ago,
            "uniqname":"one_item", "usedprice":1400, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":-0.07, "storename":SURUGAYA,
        },
        {
            "url_id": 2, "created_at":three_days_ago,
            "uniqname":"two_item", "usedprice":1200, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":SURUGAYA,
        },
        {
            "url_id": 2, "created_at":three_days_ago,
            "uniqname":"two_item2", "usedprice":1600, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0.33, "storename":SURUGAYA_CHIBA,
        },
        {
            "url_id": 3, "created_at":three_days_ago,
            "uniqname":"three_item", "usedprice":3000, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":NETOFF_HAURU,
        },
        {
            "url_id": 4, "created_at":three_days_ago,
            "uniqname":"four_item", "usedprice":3300, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":BOOKOFF_SENTOCHIHIRO,
        },
                {
            "url_id": 1, "created_at":datetime.utcnow(),
            "uniqname":"one_item", "usedprice":1400, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":SURUGAYA,
        },
        {
            "url_id": 2, "created_at":datetime.utcnow(),
            "uniqname":"two_item", "usedprice":1000, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":-0.17, "storename":SURUGAYA,
        },
        {
            "url_id": 2, "created_at":datetime.utcnow(),
            "uniqname":"two_item2", "usedprice":1600, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0.6, "storename":SURUGAYA_CHIBA,
        },
        {
            "url_id": 3, "created_at":datetime.utcnow(),
            "uniqname":"three_item", "usedprice":3300, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0.1, "storename":NETOFF_HAURU,
        },
        {
            "url_id": 4, "created_at":datetime.utcnow(),
            "uniqname":"four_item", "usedprice":3600, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0.09, "storename":BOOKOFF_SENTOCHIHIRO,
        },
    ]

    insert_item_dict_list(db, item_list=item_list)
    insert_url_dict_list(db, url_list=url_list)
    insert_urlinitem_dict_list(db, urlinitem_list=urlinitem_list)
    insert_pricelog_dict_list_sync(db, pldict_list=pricelog_list)


def add_extract_store_data_set_1(db):
    item_list = [
        {"item_id":1, "name":"one_item"},
        {"item_id":2, "name":"two_item"},
        {"item_id":3, "name":"three_item"},
    ]
    url_list = [
        {"url_id":1, "urlpath":SURUGAYA_OTHER_GEDOSENKI},
        {"url_id":2, "urlpath":SURUGAYA_OTHER_RAPYUTA},
        {"url_id":3, "urlpath":NETOFF_HAURU},
        {"url_id":4, "urlpath":BOOKOFF_SENTOCHIHIRO},
        {"url_id":5, "urlpath":SURUGAYA_OTHER_KOKURIKO},
    ]
    urlinitem_list = [
        {"item_id":1, "url_id":1, "active":"True"},
        {"item_id":1, "url_id":2, "active":"True"},
        {"item_id":2, "url_id":3, "active":"False"},
        {"item_id":2, "url_id":4, "active":"True"},
        {"item_id":3, "url_id":5, "active":"False"},
    ]
    pricelog_list = [
        {
            "url_id": 1, "created_at":dbtimeTodatetime("2023-08-22 10:00:00"),
            "uniqname":"one_item", "usedprice":1500, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":SURUGAYA,
        },
        {
            "url_id": 2, "created_at":dbtimeTodatetime("2023-08-22 10:01:00"),
            "uniqname":"two_item", "usedprice":1200, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0.177, "storename":SURUGAYA,
        },
        {
            "url_id": 3, "created_at":dbtimeTodatetime("2023-08-22 10:02:00"),
            "uniqname":"three_item", "usedprice":3000, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":-0.07, "storename":SURUGAYA,
        },
        {
            "url_id": 4, "created_at":dbtimeTodatetime("2023-08-22 10:03:00"),
            "uniqname":"four_item", "usedprice":3300, "newprice":3400,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":SURUGAYA,
        },
        {
            "url_id": 5, "created_at":dbtimeTodatetime("2023-08-22 10:04:00"),
            "uniqname":"five_item", "usedprice":-1, "newprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "issuccess":True, "trendrate":0, "storename":SURUGAYA,
        },
    ]
    newestitem_list = [
        {
            "item_id":1, "url_id": 1, "created_at":dbtimeTodatetime("2023-08-22 10:00:00"),
            "newestprice":1500,
            "taxin":True, "onsale":False, "salename":None,
            "trendrate":0, "storename":SURUGAYA,
            "lowestprice":1500,
        },
        {
            "item_id":2, "url_id": 3, "created_at":dbtimeTodatetime("2023-08-22 10:01:00"),
            "newestprice":1200,
            "taxin":True, "onsale":False, "salename":None,
            "trendrate":0.177, "storename":SURUGAYA,
            "lowestprice":1000,
        },
        {
            "item_id":3, "url_id": 5, "created_at":dbtimeTodatetime("2023-08-22 10:02:00"),
            "newestprice":-1,
            "taxin":True, "onsale":False, "salename":None,
            "trendrate":0.0, "storename":SURUGAYA,
            "lowestprice":2800,
        },
    ]
    insert_item_dict_list(db, item_list=item_list)
    insert_url_dict_list(db, url_list=url_list)
    insert_urlinitem_dict_list(db, urlinitem_list=urlinitem_list)
    insert_pricelog_dict_list_sync(db, pldict_list=pricelog_list)
    insert_newestitem_dict_list(db, nidict_list=newestitem_list)
    add_data_store(db)
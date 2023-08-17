from datetime import datetime
from fastapi.testclient import TestClient

from main import app

from common import filter_name

from tests.test_db import test_db, drop_test_db
from tests.routers.test_common import (
    RedirectCheckValue,
    check_redirect,
    is_html,
)
from tests.test_sqlalchemy import (
    insert_item_and_newestitem,
    insert_pricelog_sync,
    insert_stores,
    update_newestitem,
)
from proc import getAndWrite

client = TestClient(app)
prefix = '/calcitemcomb'

SURUGAYA_PRODUCT_NAUSHIKA="https://www.suruga-ya.jp/product/detail/128010205"
SURUGAYA_OTHER_NAUSHIKA="https://www.suruga-ya.jp/product-other/128010205"

def test_read_select_item_price_combination_no_item(test_db):
    response = client.get(f'{prefix}/select/')
    assert response.status_code == 200
    is_html(response.text)
    assert "価格計算の対象アイテムの選択" in response.text

def add_item_and_store(db):
    item_dict = {"name":"test_item", "url":SURUGAYA_OTHER_NAUSHIKA}
    pldict = {
        'url_id':1,
        'created_at':datetime.utcnow(),
        'uniqname':'test_uniq_name',
        'usedprice':1500,
        'newprice':-1,
        'taxin':True,
        'onsale':False,
        'salename':'',
        'issuccess':True,
        'storename':'駿河屋',
        'trendrate':0.0,
    }
    storename_list = ["駿河屋"]
    insert_item_and_newestitem(db=db, item_name=item_dict["name"], url_path=item_dict["url"])
    insert_pricelog_sync(db, pldict=pldict)
    nidict = getAndWrite.convert_newestitem(pldict.copy())
    update_newestitem(db, nidict=nidict)
    insert_stores(db,storename_list=storename_list)
    

def test_read_select_item_price_combination_exist_item(test_db):
    add_item_and_store(test_db)

    response = client.get(f'{prefix}/select/')
    assert response.status_code == 200
    is_html(response.text)
    assert "価格計算の対象アイテムの選択" in response.text
    assert "test_item" in response.text

    drop_test_db()

def test_read_input_shop_shipping_condition_no_query(test_db):
    response = client.get(f'{prefix}/shipping/')
    assert response.status_code == 200
    is_html(response.text)
    assert "送料条件の入力" in response.text
    assert "アイテムが指定されていません" in response.text

def test_read_input_shop_shipping_condition_exist_store(test_db):
    add_item_and_store(test_db)

    params = {filter_name.ItemDetailQueryName.ITEMID.value:1}
    response = client.get(
        f'{prefix}/shipping/',
        params=params
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "送料条件の入力" in response.text
    assert "駿河屋" in response.text

    drop_test_db()

def test_read_item_price_combination_result_no_data(test_db):
    response = client.post(f'{prefix}/result/')
    assert response.status_code == 422

def create_post_data_for_store_condition():
    store_id = 1
    terms_index = 1
    POST_STORE_NAME = filter_name.ItemCombPostKey.STORENAME
    BOUNDARY = filter_name.ItemCombPostKey.BOUNDARY
    B_OPE = filter_name.ItemCombPostKey.OPE
    POSTAGE = filter_name.ItemCombPostKey.POSTAGE
    results = {
        filter_name.TemplatePostName.ITEM_ID.value:1,
        f"stores[{store_id}][{POST_STORE_NAME}]":"駿河屋",
        f"stores[{store_id}][terms][{terms_index}][{BOUNDARY}][]":0,
        f"stores[{store_id}][terms][{terms_index}][{B_OPE}][]":"ge",
        f"stores[{store_id}][terms][{terms_index}][{POSTAGE}][]":0,
    }

    return results

def test_read_item_price_combination_result_one_item(test_db):
    add_item_and_store(test_db)

    response = client.post(
        f'{prefix}/result/',
        data=create_post_data_for_store_condition(),
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "価格計算の結果" in response.text
    price = 1500
    assert f"合計価格（送料込み）：￥{price}" in response.text

    drop_test_db()


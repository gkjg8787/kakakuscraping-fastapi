from datetime import datetime, timezone
from fastapi.testclient import TestClient

from main import app

from common import filter_name

from tests.test_db import test_db
from tests.test_routers.test_common import (
    RedirectCheckValue,
    check_redirect,
    is_html,
)
from tests.test_sqlalchemy import (
    insert_item_dict,
    insert_url,
    insert_urlinitem_dict,
    insert_newestitem_dict,
    insert_pricelog_sync,
    insert_stores,
    delete_item_and_store_model,
)
from itemcomb.itemcomb_error import ItemCombError

client = TestClient(app)
prefix = "/calcitemcomb"

SURUGAYA_PRODUCT_NAUSHIKA = "https://www.suruga-ya.jp/product/detail/128010205"
SURUGAYA_OTHER_NAUSHIKA = "https://www.suruga-ya.jp/product-other/128010205"


def test_read_select_item_price_combination_no_item(test_db):
    response = client.get(f"{prefix}/select/")
    assert response.status_code == 200
    is_html(response.text)
    assert "価格計算の対象アイテムの選択" in response.text


def add_item_no_log(db):
    item_dict = {"item_id": 1, "name": "test_item"}
    insert_item_dict(db, item_dict)


def add_item_no_store(db):
    item_dict = {"item_id": 1, "name": "test_item"}
    url_dict = {"url_id": 1, "urlpath": SURUGAYA_OTHER_NAUSHIKA}
    urlinitem_dict = {"item_id": 1, "url_id": 1, "active": "True"}
    pldict = {
        "url_id": 1,
        "created_at": datetime.now(timezone.utc),
        "uniqname": "test_uniq_name",
        "usedprice": 1500,
        "newprice": -1,
        "taxin": True,
        "onsale": False,
        "salename": "",
        "issuccess": True,
        "storename": "",
        "trendrate": 0.0,
    }
    nidict = {
        "item_id": 1,
        "url_id": 1,
        "newestprice": 1500,
        "taxin": True,
        "onsale": False,
        "salename": "",
        "trendrate": 0.0,
        "storename": "",
        "lowestprice": 1500,
    }
    insert_item_dict(db, item_dict)
    insert_url(db, url_id=url_dict["url_id"], urlpath=url_dict["urlpath"])
    insert_urlinitem_dict(db, urlinitem_dict=urlinitem_dict)
    insert_pricelog_sync(db, pldict=pldict)
    insert_newestitem_dict(db, nidict=nidict)


def add_item_and_store(db):
    # item_dict = {"name":"test_item", "url":SURUGAYA_OTHER_NAUSHIKA}
    item_dict = {"item_id": 1, "name": "test_item"}
    url_dict = {"url_id": 1, "urlpath": SURUGAYA_OTHER_NAUSHIKA}
    urlinitem_dict = {"item_id": 1, "url_id": 1, "active": "True"}
    pldict = {
        "url_id": 1,
        "created_at": datetime.now(timezone.utc),
        "uniqname": "test_uniq_name",
        "usedprice": 1500,
        "newprice": -1,
        "taxin": True,
        "onsale": False,
        "salename": "",
        "issuccess": True,
        "storename": "駿河屋",
        "trendrate": 0.0,
    }
    nidict = {
        "item_id": 1,
        "url_id": 1,
        "newestprice": 1500,
        "taxin": True,
        "onsale": False,
        "salename": "",
        "trendrate": 0.0,
        "storename": "駿河屋",
        "lowestprice": 1500,
    }
    storename_list = ["駿河屋"]
    insert_item_dict(db, item_dict)
    insert_url(db, url_id=url_dict["url_id"], urlpath=url_dict["urlpath"])
    insert_urlinitem_dict(db, urlinitem_dict=urlinitem_dict)
    insert_pricelog_sync(db, pldict=pldict)
    insert_newestitem_dict(db, nidict=nidict)
    insert_stores(db, storename_list=storename_list)


def test_read_select_item_price_combination_exist_item(test_db):
    add_item_and_store(test_db)

    response = client.get(f"{prefix}/select/")
    assert response.status_code == 200
    is_html(response.text)
    assert "価格計算の対象アイテムの選択" in response.text
    assert "test_item" in response.text

    delete_item_and_store_model(test_db)


def test_read_input_shop_shipping_condition_no_query(test_db):
    response = client.get(f"{prefix}/shipping/")
    assert response.status_code == 200
    is_html(response.text)
    assert "送料条件の入力" in response.text
    assert "アイテムが指定されていません" in response.text


def test_read_input_shop_shipping_condition_no_today_log(test_db):
    add_item_no_log(test_db)

    params = {filter_name.ItemDetailQueryName.ITEMID.value: 1}
    response = client.get(f"{prefix}/shipping/", params=params)
    assert response.status_code == 200
    is_html(response.text)
    assert "送料条件の入力" in response.text
    assert ItemCombError.NO_TODAY_LOG.value in response.text

    delete_item_and_store_model(test_db)


def test_read_input_shop_shipping_condition_no_store(test_db):
    add_item_no_store(test_db)

    params = {filter_name.ItemDetailQueryName.ITEMID.value: 1}
    response = client.get(f"{prefix}/shipping/", params=params)
    assert response.status_code == 200
    is_html(response.text)
    assert "送料条件の入力" in response.text
    assert ItemCombError.NO_STORE_DATA.value in response.text

    delete_item_and_store_model(test_db)


def test_read_input_shop_shipping_condition_exist_store(test_db):
    add_item_and_store(test_db)

    params = {filter_name.ItemDetailQueryName.ITEMID.value: 1}
    response = client.get(f"{prefix}/shipping/", params=params)
    assert response.status_code == 200
    is_html(response.text)
    assert "送料条件の入力" in response.text
    assert "駿河屋" in response.text

    delete_item_and_store_model(test_db)


def test_read_item_price_combination_result_no_data(test_db):
    response = client.post(f"{prefix}/result/")
    assert response.status_code == 422


def create_post_data_for_store_condition():
    store_id = 1
    terms_index = 1
    POST_STORE_NAME = filter_name.ItemCombPostKey.STORENAME
    BOUNDARY = filter_name.ItemCombPostKey.BOUNDARY
    B_OPE = filter_name.ItemCombPostKey.OPE
    POSTAGE = filter_name.ItemCombPostKey.POSTAGE
    results = {
        filter_name.TemplatePostName.ITEM_ID.value: 1,
        f"stores[{store_id}][{POST_STORE_NAME}]": "駿河屋",
        f"stores[{store_id}][terms][{terms_index}][{BOUNDARY}][]": 0,
        f"stores[{store_id}][terms][{terms_index}][{B_OPE}][]": "ge",
        f"stores[{store_id}][terms][{terms_index}][{POSTAGE}][]": 0,
    }

    return results


def test_read_item_price_combination_result_one_item(test_db):
    add_item_and_store(test_db)

    response = client.post(
        f"{prefix}/result/",
        data=create_post_data_for_store_condition(),
    )
    assert response.status_code == 200
    is_html(response.text)
    assert "価格計算の結果" in response.text
    price = 1500
    assert f"合計価格（送料込み）：￥{price}" in response.text

    delete_item_and_store_model(test_db)


def test_read_input_search_shop_shipping_top(test_db):
    response = client.get(
        f"{prefix}/shipping/search/",
    )
    assert response.status_code == 200
    is_html(response.text)
    assert "送料検索ツール" in response.text


def test_read_input_search_shop_shipping_no_word(test_db):
    params = {filter_name.FilterQueryName.WORD.value: ""}
    response = client.get(f"{prefix}/shipping/search/", params=params)
    assert response.status_code == 200
    is_html(response.text)
    assert "送料検索ツール" in response.text
    assert "検索ワードが指定されていません" in response.text


def test_read_input_search_shop_shipping_search_store(test_db):
    storename = "秋葉原本館"
    params = {filter_name.FilterQueryName.WORD.value: storename}
    response = client.get(f"{prefix}/shipping/search/", params=params)
    assert response.status_code == 200
    is_html(response.text)
    assert "送料検索ツール" in response.text
    assert f"店名：{storename}" in response.text

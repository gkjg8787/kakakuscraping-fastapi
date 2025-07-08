import json
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient

from main import app
from domain.models.items import items
from tests.test_db import test_db, drop_test_db
from tests.test_sqlalchemy import (
    insert_pricelog_sync,
)

client = TestClient(app)
prefix = "/api"


def test_api_add_item_one_url(test_db):
    try:
        item = items.ItemCreate(
            name="マリオカートワールド",
            urls=["https://ec.geo-online.co.jp/shop/g/g517310102/"],
        )
        result = items.ItemCreateResponse(**item.model_dump(), item_id=1)
        response = client.post(
            f"{prefix}/items/", json=json.loads(item.model_dump_json())
        )
        assert response.status_code == 200
        assert response.json() == result.model_dump()
    finally:
        drop_test_db()


def test_api_add_item_two_url(test_db):
    try:
        item = items.ItemCreate(
            name="マリオカートワールド",
            urls=[
                "https://ec.geo-online.co.jp/shop/g/g517310102/",
                "https://ec.geo-online.co.jp/shop/g/g517310101/",
            ],
        )
        result = items.ItemCreateResponse(**item.model_dump(), item_id=1)
        response = client.post(
            f"{prefix}/items/", json=json.loads(item.model_dump_json())
        )
        assert response.status_code == 200
        assert response.json() == result.model_dump()
    finally:
        drop_test_db()


def test_api_update_item_url_active(test_db):
    target_urls = [
        "https://ec.geo-online.co.jp/shop/g/g517310102/",
        "https://ec.geo-online.co.jp/shop/g/g517310101/",
    ]
    item_id = 1
    try:
        item = items.ItemCreate(
            name="マリオカートワールド",
            urls=target_urls,
        )
        result = items.ItemCreateResponse(**item.model_dump(), item_id=item_id)
        response = client.post(
            f"{prefix}/items/", json=json.loads(item.model_dump_json())
        )
        assert response.status_code == 200
        assert response.json() == result.model_dump()

        is_active = False
        urlacts = [items.URLActive(url=target_urls[0], is_active=is_active)]
        item = items.ItemUpdate(item_id=item_id, name=None, url_actives=urlacts)
        result = items.ItemUpdateResponse(**item.model_dump())
        response = client.patch(
            f"{prefix}/items/", json=json.loads(item.model_dump_json())
        )
        assert response.status_code == 200
        assert response.json() == result.model_dump()

        is_active = True
        for u in urlacts:
            u.is_active = is_active
        item = items.ItemUpdate(item_id=item_id, name=None, url_actives=urlacts)
        result = items.ItemUpdateResponse(**item.model_dump())
        response = client.patch(
            f"{prefix}/items/", json=json.loads(item.model_dump_json())
        )
        assert response.status_code == 200
        assert response.json() == result.model_dump()

    finally:
        drop_test_db()


def test_api_update_item_name(test_db):
    target_urls = ["https://ec.geo-online.co.jp/shop/g/g517310102/"]
    item_id = 1
    name = "マリオカートワールド"
    try:
        item = items.ItemCreate(
            name=name,
            urls=target_urls,
        )
        result = items.ItemCreateResponse(**item.model_dump(), item_id=item_id)
        response = client.post(
            f"{prefix}/items/", json=json.loads(item.model_dump_json())
        )
        assert response.status_code == 200
        assert response.json() == result.model_dump()

        is_active = True
        to_name = "マリカ"
        urlacts = [items.URLActive(url=u, is_active=is_active) for u in target_urls]
        item = items.ItemUpdate(item_id=item_id, name=to_name, url_actives=urlacts)
        result = items.ItemUpdateResponse(**item.model_dump())
        response = client.patch(
            f"{prefix}/items/", json=json.loads(item.model_dump_json())
        )
        assert response.status_code == 200
        assert response.json() == result.model_dump()

    finally:
        drop_test_db()


def test_api_add_items_url(test_db):
    target_urls = ["https://ec.geo-online.co.jp/shop/g/g517310102/"]
    add_urls = ["https://ec.geo-online.co.jp/shop/g/g517310101/"]
    item_id = 1
    url_id = 2
    name = "マリオカートワールド"
    try:
        item = items.ItemCreate(
            name=name,
            urls=target_urls,
        )
        result = items.ItemCreateResponse(**item.model_dump(), item_id=item_id)
        response = client.post(
            f"{prefix}/items/", json=json.loads(item.model_dump_json())
        )
        assert response.status_code == 200
        assert response.json() == result.model_dump()

        is_active = False
        urlacts = [items.URLActive(url=u, is_active=is_active) for u in add_urls]
        item = items.ItemsURLCreate(item_id=item_id, url_actives=urlacts)
        res_urlacts = [
            items.DBURLActive(url_id=url_id, url=u.url, is_active=u.is_active)
            for u in urlacts
        ]
        result = items.ItemsURLCreateResponse(item_id=item_id, url_actives=res_urlacts)
        response = client.post(
            f"{prefix}/items/urls/", json=json.loads(item.model_dump_json())
        )
        assert response.status_code == 200
        assert response.json() == result.model_dump()

    finally:
        drop_test_db()


"""
def test_api_update_price(test_db):
    target_urls = [
        "https://ec.geo-online.co.jp/shop/g/g517310102/",
        "https://ec.geo-online.co.jp/shop/g/g517310101/",
    ]
    item_id = 1
    url_id = 1
    pldict = {
        "url_id": 1,
        "created_at": datetime.now(timezone.utc) - timedelta(days=1),
        "uniqname": "test_uniq_name",
        "usedprice": 7980,
        "newprice": -1,
        "taxin": True,
        "onsale": False,
        "salename": "",
        "issuccess": True,
        "storename": "ゲオ",
        "trendrate": 0.0,
    }

    def test_func():
        item = items.ItemCreate(
            name="マリオカートワールド",
            urls=target_urls,
        )
        result = items.ItemCreateResponse(**item.model_dump(), item_id=item_id)
        response = client.post(
            f"{prefix}/items/", json=json.loads(item.model_dump_json())
        )
        assert response.status_code == 200
        assert response.json() == result.model_dump()

        insert_pricelog_sync(test_db, pldict)

        pinfo = items.ParseInfo(
            url=target_urls[0],
            name=pldict["uniqname"],
            price=7700,
            condition="中古",
            taxin=True,
            on_sale=False,
            salename="",
            timestamp=datetime.now(timezone.utc),
            is_success=True,
            storename="ゲオ",
        )
        pis = items.ParseInfosUpdate(infos=[pinfo])
        response = client.patch(
            f"{prefix}/price/", json=json.loads(pis.model_dump_json())
        )
        dbpinfo = items.DBParseInfo(url_id=url_id, **pinfo.model_dump())
        dbpis = items.ParseInfosUpdateResponse(infos=[dbpinfo])
        assert response.status_code == 200
        assert response.json() == json.loads(dbpis.model_dump_json())

    try:
        test_func()
    finally:
        drop_test_db()
"""

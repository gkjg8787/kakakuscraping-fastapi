import sys
from os.path import dirname
import random
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

parent_dir = dirname(dirname(__file__))
sys.path.append(parent_dir)
from common import const_value, util as cm_util
from accessor.read_sqlalchemy import get_session
from accessor.item.item import NewestQuery, ItemQuery, UrlQuery, OrganizerQuery

DEFAULT_STORENAME = "駿河屋"


def get_base_maricar():
    results = {
        "item_name": "マリオカート8",
        "url": "https://www.suruga-ya.jp/product/other/109000004",
        "uniqname": "マリオカート8 デラックス",
        "used_range_min": 3300,
        "used_range_max": 4700,
        "new_range_min": 5180,
        "new_range_max": 5500,
        "data_length": 40,
        "seed": 0,
        "add_urls": ["https://www.suruga-ya.jp/product/other/109003254"],
    }
    return results


def get_base_totoro():
    results = {
        "item_name": "トトロ",
        "url": "https://www.suruga-ya.jp/product/other/128002938",
        "uniqname": "となりのトトロ",
        "used_range_min": 2000,
        "used_range_max": 4000,
        "data_length": 20,
        "seed": 0,
    }
    return results


def create_sample_data(base_data: dict):
    def create_itemsprice(base_data: dict, seed: int):
        random.seed(seed)
        itemsprice_used = [
            random.randint(base_data["used_range_min"], base_data["used_range_max"])
            for _ in range(base_data["data_length"])
        ]
        if "new_range_min" in base_data and "new_range_max" in base_data:
            itemsprice_new = [
                random.randint(base_data["new_range_min"], base_data["new_range_max"])
                for _ in range(base_data["data_length"])
            ]
        else:
            itemsprice_new = [
                const_value.INIT_PRICE for _ in range(base_data["data_length"])
            ]
        itemsprice: list[dict] = []
        for used, new in zip(itemsprice_used, itemsprice_new):
            data = {
                "uniqname": base_data["uniqname"],
                "usedprice": used,
                "newprice": new,
            }
            itemsprice.append(data)
        return itemsprice

    itemsprice = create_itemsprice(base_data=base_data, seed=base_data["seed"])
    results = {
        "item_name": base_data["item_name"],
        "url_path": base_data["url"],
        "itemsprice": itemsprice,
    }
    if "add_urls" not in base_data:
        return results

    for num, url in enumerate(base_data["add_urls"]):
        add_itemsprice = create_itemsprice(
            base_data=base_data, seed=base_data["seed"] + num + 1
        )
        ret = {"url_path": url, "itemsprice": add_itemsprice}
        if "add_urls" not in results:
            results["add_urls"] = [ret]
        else:
            results["add_urls"].append(ret)
    return results


def create_pldict(url_id: int, itemsprice_record: dict, days_ago: int):
    now = datetime.now(timezone.utc)
    jst_now = cm_util.utcTolocaltime(now)
    jst_now -= timedelta(days=days_ago)
    d = jst_now.astimezone(tz=timezone.utc)
    d = d.replace(tzinfo=None)
    pldict = {
        "url_id": url_id,
        "uniqname": itemsprice_record["uniqname"],
        "usedprice": itemsprice_record["usedprice"],
        "newprice": itemsprice_record["newprice"],
        "taxin": 1,
        "onsale": 0,
        "salename": "",
        "issuccess": 1,
        "trendrate": 0.0,
        "storename": DEFAULT_STORENAME,
        "created_at": d,
    }
    return pldict


def create_nidict(url_id: int, itemsprice_record: dict):
    ret = {
        "url_id": url_id,
        "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
        "newestprice": itemsprice_record["usedprice"],
        "taxin": 1,
        "onsale": 0,
        "salename": 1,
        "trendrate": 0.0,
        "storename": DEFAULT_STORENAME,
    }
    return ret


def insert_pricelog(db, itemsprice_list: list, url: str):
    url_id = UrlQuery.get_url_id_by_url(db=db, url=url)
    max_len = len(itemsprice_list)
    for idx, ip in zip(range(max_len - 1, -1, -1), itemsprice_list):
        pldict = create_pldict(url_id=url_id, itemsprice_record=ip, days_ago=idx)
        OrganizerQuery.add_price_log_by_dict_list(db=db, pricelog_dict_list=pldict)
        if idx == 0:
            OrganizerQuery.add_price_log_2days_by_dict_list(
                db=db, pricelog_dict_list=pldict
            )
            nidict = create_nidict(url_id=url_id, itemsprice_record=ip)
            NewestQuery.update_items_by_dict(db=db, nidict=nidict)


def add_sample_data(db):
    target_base_list = [
        get_base_totoro(),
        get_base_maricar(),
    ]
    for idx, target_base in enumerate(target_base_list):
        data_dict = create_sample_data(target_base)
        NewestQuery.add_item(
            item_name=data_dict["item_name"], url_path=data_dict["url_path"], db=db
        )
        insert_pricelog(
            db=db, itemsprice_list=data_dict["itemsprice"], url=data_dict["url_path"]
        )

        if "add_urls" not in data_dict:
            continue

        for add_url in data_dict["add_urls"]:
            item_id = idx + 1
            UrlQuery.add_url_and_urlinitem(
                db=db, urlpath=add_url["url_path"], item_id=item_id
            )
            insert_pricelog(
                db=db, itemsprice_list=add_url["itemsprice"], url=add_url["url_path"]
            )


def is_exist_data(db):
    ret = NewestQuery.get_raw_newest_data_all(db)
    if ret:
        return True
    return False


def main(argv):
    with next(get_session()) as db:
        if is_exist_data(db=db):
            print("既にデータが存在するためサンプルを追加しませんでした。")
            return
        add_sample_data(db=db)


if __name__ == "__main__":
    main(sys.argv)

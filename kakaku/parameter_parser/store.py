from typing import Dict, List
from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.filter_name import (
    FilterQueryName,
)
from common.templates_string import HTMLOption

from accessor.item import NewestQuery, ItemQuery
from accessor.store import StoreQuery


class TemplatesStore(BaseModel):
    id: int
    name: str
    selected: str = ""


def get_stores(db: Session, f: dict):
    results = [
        TemplatesStore(id=s.store_id, name=s.storename) for s in StoreQuery.get_all(db)
    ]
    if FilterQueryName.STORE.value not in f:
        return results
    for r in results:
        if r.id == int(f[FilterQueryName.STORE.value]):
            r.selected = HTMLOption.SELECTED.value
            break
    return results


def get_stores_for_newest(db: Session, filter: dict):
    return get_selected_store_list(
        db,
        filter=filter,
        filter_key_name=FilterQueryName.STORE.value,
        target_store_result=NewestQuery.get_storenames(db),
    )


def get_stores_for_extract_store(db: Session, filter: dict):
    return get_selected_store_list(
        db,
        filter=filter,
        filter_key_name=FilterQueryName.EX_STORE.value,
        target_store_result=ItemQuery.get_newest_storenames(db),
    )


def get_selected_store_list(
    db: Session, filter: dict, filter_key_name: str, target_store_result: list
):
    store_all = [
        TemplatesStore(id=s.store_id, name=s.storename) for s in StoreQuery.get_all(db)
    ]
    newest_store_list = __get_newest_store_list(target_store_result)
    results = [r for r in store_all if r.name in newest_store_list]
    return get_sorted_selected_store_list(
        filter=filter, filter_key_name=filter_key_name, store_list=results
    )


def get_sorted_selected_store_list(
    filter: dict, filter_key_name: str, store_list: list[TemplatesStore]
):
    results = sorted(store_list, key=lambda r: r.name)

    if (
        filter_key_name not in filter
        or not filter[filter_key_name]
        or int(filter[filter_key_name]) < 0
    ):
        return results
    store_id = int(filter[filter_key_name])
    for r in results:
        if r.id == store_id:
            r.selected = HTMLOption.SELECTED.value
            break
    return results


def __get_newest_store_list(newest_list: list):
    results = []
    for row in newest_list:
        for k, v in row._mapping.items():
            if "storename" == k and v and len(v) > 0:
                results.append(v)
    return results


def get_stores_for_item_detail(
    db: Session, filter: dict, storename_list: list[str]
) -> list[TemplatesStore]:
    if not storename_list:
        return []
    store_list = [
        TemplatesStore(id=s.store_id, name=s.storename)
        for s in StoreQuery.get_store_by_storename_list(
            db=db, storename_list=storename_list
        )
    ]
    return get_sorted_selected_store_list(
        filter=filter,
        filter_key_name=FilterQueryName.STORE.value,
        store_list=store_list,
    )

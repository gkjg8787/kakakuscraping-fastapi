from typing import Dict, List
from pydantic import BaseModel

from common.filter_name import (
    FilterQueryName,
)
from common.templates_string import HTMLOption

from accessor.item import NewestQuery
from accessor.store import StoreQuery

class TemplatesStore(BaseModel):
    id: int
    name: str
    selected: str = ''

def get_stores(f:Dict) -> List:
    results = [TemplatesStore(id=s.store_id, name=s.storename) for s in StoreQuery.get_all()]
    if not FilterQueryName.STORE.value in f:
        return results
    for r in results:
        if r.id == int(f[FilterQueryName.STORE.value]):
            r.selected = HTMLOption.SELECTED.value
            break
    return results

def get_stores_for_newest(filter :Dict) -> List:
    results = [TemplatesStore(id=s.store_id, name=s.storename) for s in StoreQuery.get_all()]
    newest_store_list = __get_newest_store_list(NewestQuery.get_storenames())
    results = [r for r in results if r.name in newest_store_list ]

    if not FilterQueryName.STORE.value in filter \
        or not filter[FilterQueryName.STORE.value] \
        or int(filter[FilterQueryName.STORE.value]) < 0:
        return results
    store_id = int(filter[FilterQueryName.STORE.value])
    for r in results:
        if r.id == store_id:
            r.selected = HTMLOption.SELECTED.value
            break
    return results

def __get_newest_store_list(newest_list :List) -> List:
    results = []
    for row in newest_list:
        for k, v in row._mapping.items():
            if 'storename' == k and v and len(v) > 0:
                results.append(v)
    return results
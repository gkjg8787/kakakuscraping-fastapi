from typing import List

from fastapi import Query, Form
from pydantic import BaseModel

from parameter_parser.util import is_valid_id
from parameter_parser.storepostage import ItemCombStore, FormDataConvert


class ShippingConditionQuery:
    item_id_list: List[int] = []
    errmsg: str = ""

    def __init__(
        self,
        itemid: List[str] = Query(None),
    ):
        if itemid:
            results: List[int] = []
            for id in itemid:
                if is_valid_id(id):
                    results.append(int(id))
            self.item_id_list = results

    def is_valid(self):
        if len(self.item_id_list) == 0:
            self.errmsg = "アイテムが指定されていません"
            return False
        return True


class ItemCombinationResultForm(BaseModel):
    item_id_list: List[int] = []
    store_list: List[ItemCombStore] = []
    errmsg: str = ""

    def __init__(
        self,
        item_id: List[str] = Form(),
    ):
        super().__init__()
        if item_id:
            results: List[int] = []
            for id in item_id:
                if is_valid_id(id):
                    results.append(int(id))
            self.item_id_list = results

    def is_valid(self):
        if len(self.item_id_list) == 0:
            self.errmsg = "アイテムが指定されていません"
            return False
        return True

    def set_store_list(self, stores: list[str]):
        if stores:
            self.store_list = FormDataConvert.parse_stores(stores)


class SearchShippingQuery:
    word: str = ""
    pref: str = ""
    errmsg: str = ""

    def __init__(
        self,
        word: str = "",
        pref: str = "",
    ):
        if word:
            self.word = word
        if pref:
            self.pref = pref

    def is_valid(self):
        if not self.word:
            self.errmsg = "検索ワードが指定されていません"
            return False
        return True

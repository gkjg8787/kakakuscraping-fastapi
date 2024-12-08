from fastapi import Query, Form
from pydantic import BaseModel

from parameter_parser.util import is_valid_id
from parameter_parser.storepostage import ItemCombStore, FormDataConvert
from common import filter_name


class ShippingConditionQuery:
    item_id_list: list[int] = []
    sort: str = str(filter_name.StoreListSortName.OLD_STORE.id)
    errmsg: str = ""

    def __init__(
        self,
        itemid: list[str] = Query(None),
        sort: str = "",
    ):
        if sort and sort.isdigit() and filter_name.StoreListSortName.hasId(int(sort)):
            self.sort = sort
        if itemid:
            results: list[int] = []
            for id in itemid:
                if is_valid_id(id):
                    results.append(int(id))
            self.item_id_list = results

    def is_valid(self):
        if len(self.item_id_list) == 0:
            self.errmsg = "アイテムが指定されていません"
            return False
        return True

    def get_filter_dict(self) -> dict:
        results = {}
        if self.sort:
            results[filter_name.FilterQueryName.SORT.value] = self.sort
        return results

    def get_cookie(self) -> str:
        return str(self.item_id_list)


class ItemCombinationResultForm(BaseModel):
    item_id_list: list[int] = []
    store_list: list[ItemCombStore] = []
    errmsg: str = ""

    def __init__(
        self,
        item_id: list[str] = Form(),
    ):
        super().__init__()
        if item_id:
            results: list[int] = []
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

from typing import Dict, List, Union, Optional

from fastapi import Query, Cookie, Form

from common.filter_name import (
    FilterQueryName,
    FilterDefault,
    FilterOnOff,
)
from common import const_value
from parameter_parser.util import is_valid_id, is_suppoer_url

class SearchFilterQuery():
    word :str = ""
    page :int = FilterDefault.PAGE
    stores :List[int] = FilterDefault.STORES_SEARCH
    category :int = FilterDefault.CATEGORY
    safes :int = FilterDefault.SAFE_SEARCH
    zaiko :int = FilterDefault.ZAIKO
    listview :int = FilterDefault.LIST_VIEW

    setting_list :list[FilterQueryName] = []

    def __init__(self,
                 word :Optional[str] = None,
                 page :Optional[str] = None,
                 store :List[str] = Query(None),
                 category :Optional[str] = None,
                 safes :Optional[str] = None,
                 zaiko :Optional[str] = None,
                 listview :Optional[str] = None,
                 ):
        self.setting_list = []
        if word and len(word) > 0:
            self.word = word
            self.setting_list.append(FilterQueryName.WORD)
        if is_valid_positive_int(page):
            self.page = page
            self.setting_list.append(FilterQueryName.PAGE)
        if store:
            results :List[int] = []
            for s in store:
                if is_valid_positive_int(s):
                    results.append(int(s))
            self.stores = results
            if len(results) > 0:
                self.setting_list.append(FilterQueryName.STORE)
        if is_valid_positive_int(category):
            self.category = int(category)
            self.setting_list.append(FilterQueryName.CATEGORY)
        if is_valid_positive_int(safes):
            self.safes = int(safes)
            self.setting_list.append(FilterQueryName.SAFES)
        if is_valid_positive_int(zaiko):
            self.zaiko = int(zaiko)
            self.setting_list.append(FilterQueryName.ZAIKO)
        if is_valid_positive_int(listview):
            self.listview = int(listview)
            self.setting_list.append(FilterQueryName.LISTVIEW)
    
    def get_query_dict(self):
        results = {}
        onoffvals = [FilterOnOff.ON, FilterOnOff.OFF]
        if self.word:
            results[FilterQueryName.WORD.value] = self.word
        if self.page:
            results[FilterQueryName.PAGE.value] = self.word
        if self.stores and len(self.stores) > 0:
            results[FilterQueryName.STORE.value] = self.stores
        if self.category:
            results[FilterQueryName.CATEGORY.value] = self.category
        if self.safes in onoffvals:
            results[FilterQueryName.SAFES.value] = self.safes
        if self.zaiko in onoffvals:
            results[FilterQueryName.ZAIKO.value] = self.zaiko
        if self.listview:
            results[FilterQueryName.LISTVIEW.value] = self.listview
        return results
    


    def get_search_dict(self):
        results = {}
        results[FilterQueryName.PAGE.value] = self.page
        if self.stores and len(self.stores) > 0:
            results[FilterQueryName.STORE.value] = self.stores
        results[FilterQueryName.CATEGORY.value] = self.category
        results[FilterQueryName.SAFES.value] = self.safes
        results[FilterQueryName.ZAIKO.value] = self.zaiko
        results["output"] = { "type":"text" }
        return results

def is_valid_positive_int(num :str) -> bool:
    return is_valid_id(num)

class SearchToAddForm():
    item_name :str = ""
    url_path :str = ""
    item_id :int = const_value.NONE_ID
    search_query :str = ""
    errmsg :str = ""
    def __init__(self,
                 item_id :Optional[str]=Form(None),
                 item_name :Optional[str]=Form(None),
                 url_path :Optional[str]=Form(None),
                 search_query:Optional[str]=Form(None),
                 ):
        if is_valid_id(item_id):
            self.item_id = int(item_id)
        if item_name:
            self.item_name = item_name
        if url_path:
            self.url_path = url_path.strip()
        if search_query:
            self.search_query = search_query
    
    def is_valid(self) -> bool:
        if self.url_path:
            if is_suppoer_url(self.url_path):
                return True
            else:
                self.errmsg = "対象外のURLです"
                return False
        self.errmsg = "URLが不明です"
        return False


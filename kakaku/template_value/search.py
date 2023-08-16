from typing import List, Dict, Optional, Union
import json

from pathlib import Path

from pydantic import BaseModel

from sqlalchemy.orm import Session

from common import (
    filter_name,
    const_value,
    templates_string,
    read_config,
)
from template_value.item import BaseTemplateValue
from parameter_parser.search import (
    SearchFilterQuery,
    SearchToAddForm,
)

from url_search.sitesearch import get_search_for_inner

from html_parser.search_parser import SearchParser
from html_parser.search_converter import SearchDictConverter, SearchResult

from accessor.item import NewestQuery


class SearchExternalSiteContext(BaseTemplateValue):
    sword :str = ""
    stores :List = []
    categorylist :List = []
    search_results :Union[SearchResult,None] = None
    safes_off_checked :str = ""
    zaiko_checked :str = ""
    listview_checked :str = ""
    search_query :str = ""
    CATEGORY_NAME :str = filter_name.FilterQueryName.CATEGORY.value
    SEARCH_WORD_NAME :str = filter_name.FilterQueryName.WORD.value
    STORE_ID_NAME :str = filter_name.FilterQueryName.STORE.value
    SAFE_SEARCH_NAME :str = filter_name.FilterQueryName.SAFES.value
    STOCK_NAME :str = filter_name.FilterQueryName.ZAIKO.value
    LIST_VIEW_NAME :str = filter_name.FilterQueryName.LISTVIEW.value
    PAGE_NAME :str = filter_name.FilterQueryName.PAGE.value
    POST_ITEM_NAME :str = filter_name.TemplatePostName.ITEM_NAME.value
    POST_URL_PATH :str = filter_name.TemplatePostName.URL_PATH.value
    POST_SEARCH_QUERY :str = filter_name.TemplatePostName.SEARCH_QUERY.value

    def __init__(self, request, sfq:SearchFilterQuery):
        super().__init__(request=request)
        optjson = self.get_option_json()
        fq = sfq.get_query_dict()
        self.categorylist = self.get_category_list(optjson, fq)
        self.stores = self.get_store_list(optjson, sfq.get_query_dict())
        if sfq.safes == filter_name.FilterOnOff.OFF:
            self.safes_off_checked = templates_string.HTMLOption.CHECKED.value
        if sfq.zaiko == filter_name.FilterOnOff.ON:
            self.zaiko_checked = templates_string.HTMLOption.CHECKED.value
        if sfq.listview == filter_name.FilterOnOff.ON:
            self.listview_checked = templates_string.HTMLOption.CHECKED.value

        if sfq.word:
            self.sword = sfq.word
            s_ret = get_search_for_inner(self.sword, sfq.get_search_dict())
            if 'errmsg' in s_ret:
                self.search_result = s_ret['errmsg']
            else:
                urlparam = sfq.get_query_dict()
                urlparam[filter_name.FilterQueryName.WORD.value] = self.sword
                pageinfo = s_ret['result'][SearchParser.PAGE]
                self.search_query = SearchDictConverter.createURLParamForTemplateValue(
                                            urlparam=urlparam,
                                            pageinfo=pageinfo,
                                            )
                self.search_results = SearchDictConverter.convertToSearchResult(
                                            items=s_ret['result'][SearchParser.ITEMS],
                                            pageinfo=pageinfo,
                                            urlparam=urlparam,
                                            )
    
    def get_category_list(self, optjson :Dict, fq :Dict):
        selected_id = None
        if filter_name.FilterQueryName.CATEGORY.value in fq:
            selected_id = fq[filter_name.FilterQueryName.CATEGORY.value]
        results = []
        category = optjson['category']['default']
        for k, v in category.items():
            scate = SearchCategory(id=int(k), jname=v)
            if selected_id and selected_id == scate.id:
                scate.selected = templates_string.HTMLOption.SELECTED.value
            results.append(scate)
        return results
    
    def get_store_list(self, optjson :Dict, fq :Dict):
        selected_id_list = None
        if filter_name.FilterQueryName.STORE.value in fq:
            selected_id_list = fq[filter_name.FilterQueryName.STORE.value]
        results = []
        stores = optjson['store']
        for k, v in stores.items():
            st = SearchStore(store_id=int(k), jname=v["jpname"])
            if selected_id_list and st.store_id in selected_id_list:
                st.checked = templates_string.HTMLOption.CHECKED.value
            results.append(st)
        return results

    @staticmethod
    def get_option_json():
        text = SearchExternalSiteContext.read_option()
        optjson = json.loads(text)
        return optjson
    
    @staticmethod
    def read_option():
        OPTION_FILE_NAME = "option.json"
        fpath = Path(read_config.get_search_option_path(), OPTION_FILE_NAME)
        with open(fpath, encoding="utf-8") as f:
            opt = f.read()
        return opt
        
class SearchCategory(BaseModel):
    id :int
    jname :str = ""
    selected :str = ""

class SearchStore(BaseModel):
    store_id :int
    jname :str = ""
    checked : str = ""
    errmsg :str = ""

class AddSelectItem(BaseModel):
    item_id :int = const_value.NONE_ID
    name :str = ""
    selected :str = ""

class SearchToAddContext(BaseTemplateValue):
    add_item_name :str = ""
    add_url_path :str = ""
    add_item_id :int = const_value.NONE_ID
    errmsg :str = ""
    itemlist :List = []
    search_query :str = ""
    POST_ITEM_ID :str = filter_name.TemplatePostName.ITEM_ID.value
    POST_ITEM_NAME :str = filter_name.TemplatePostName.ITEM_NAME.value
    POST_URL_PATH :str = filter_name.TemplatePostName.URL_PATH.value
    POST_SEARCH_QUERY :str = filter_name.TemplatePostName.SEARCH_QUERY.value

    def __init__(self, request, saform :SearchToAddForm, db :Session):
        super().__init__(request=request)
        if not saform.is_valid():
            self.errmsg = saform.errmsg
            return
        self.add_url_path = saform.url_path
        if saform.item_name:
            self.add_item_name = saform.item_name
        if saform.search_query:
            self.search_query = saform.search_query
        if saform.item_id > 0:
            self.add_item_id = saform.item_id
            item = NewestQuery.get_newest_data_by_item_id(db, item_id=self.add_item_id)
            if not item:
                self.add_item_id = const_value.NONE_ID
                msg = "指定されたIDのアイテムが存在しません"
                self.errmsg = ", ".join([self.errmsg, msg])
            else:
                itemdic = {k:v for k,v in item._mapping.items()}
                self.add_item_name = itemdic['name']
        self.itemlist = self.get_item_list(db, self.add_item_id)
    
    def get_item_list(self, db :Session, add_item_id:int):
        newest_list = NewestQuery.get_newest_data(db, filter=dict())
        results :List[AddSelectItem]= []
        if len(newest_list) == 0:
            return results
        for item in newest_list:
            d = {k:v for k,v in item._mapping.items()}
            additem = AddSelectItem(item_id=d['item_id'],
                                    name=d['name']
                                    )
            if add_item_id != const_value.NONE_ID \
                and add_item_id == additem.item_id:
                additem.selected = templates_string.HTMLOption.SELECTED.value
            results.append(additem)
        return results
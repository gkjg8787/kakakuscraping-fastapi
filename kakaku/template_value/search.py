from typing import List, Dict, Union
import json
from enum import Enum, auto

from pathlib import Path

from pydantic import BaseModel

from sqlalchemy.orm import Session

from common import (
    filter_name,
    const_value,
    templates_string,
    read_config,
)
from template_value import BaseTemplateValue
from parameter_parser.search import (
    SearchFilterQuery,
    SearchToAddForm,
)

from url_search.sitesearch import get_search_for_inner

from html_parser.search_parser import SearchParser
from html_parser.search_converter import SearchDictConverter, SearchResult

from accessor.item import NewestQuery


class SearchOptionName(Enum):
    INIT = auto()
    DISPLAY = auto()
    VALUE = auto()


class SearchOptionSetting:
    name :str = ""
    display : bool = True
    init : bool = False
    value : str = ""
    
    def __init__(self, name :str, vdic :dict):
        self.name = name
        if SearchOptionName.INIT.name in vdic:
            initv = vdic[SearchOptionName.INIT.name]
            if type(initv) is str \
                and initv.upper() == "ON":
                self.init = True
            else:
                self.init = False
        if SearchOptionName.DISPLAY.name in vdic:
            dispv = vdic[SearchOptionName.DISPLAY.name]
            if type(dispv) is str \
                and dispv.upper() == "OFF":
                self.display = False
            else:
                self.display = True
        if SearchOptionName.VALUE.name in vdic:
            vv = vdic[SearchOptionName.VALUE.name]
            if type(vv) is str\
                and len(vv) > 0:
                self.value = vv

    @staticmethod
    def create(vdic :dict, name :str):
        return SearchOptionSetting(name=name, vdic=vdic)

class StoreSelectOption(SearchOptionSetting):
    stores_dict :dict[str, bool]

    def __init__(self, name :str, vdic :dict):
        super().__init__(name=name, vdic=vdic)
        self.stores_dict = {}
        for k, v in vdic.items():
            if v.upper() == "ON":
                self.stores_dict[k] = True
            else:
                self.stores_dict[k] = False

    @staticmethod
    def create(vdic :dict, name :str):
        return StoreSelectOption(name=name, vdic=vdic)
    
    def is_checked_store(self, storename :str):
        if storename in self.stores_dict.keys():
            return self.stores_dict[storename]
        return False



class SearchOptionSettings:
    optionlist : dict[filter_name.FilterQueryName, SearchOptionSetting]

    def __init__(self):
        self.read_settings()
    
    def get_option(self, key: filter_name.FilterQueryName):
        if key in self.optionlist:
            return self.optionlist[key]
        return None

    def read_settings(self):
        self.optionlist = {}
        dic = read_config.get_search_options_default()
        for key in dic.keys():
            if key.lower() == filter_name.FilterQueryName.CATEGORY.value:
                self.optionlist[filter_name.FilterQueryName.CATEGORY] = self.create_category(dic[key])
            if key.lower() == filter_name.FilterQueryName.ZAIKO.value:
                self.optionlist[filter_name.FilterQueryName.ZAIKO] = self.create_zaiko(dic[key])
            if key.lower() == filter_name.FilterQueryName.SAFES.value:
                self.optionlist[filter_name.FilterQueryName.SAFES] = self.create_safesearch(dic[key])
            if key.lower() == filter_name.FilterQueryName.LISTVIEW.value:
                self.optionlist[filter_name.FilterQueryName.LISTVIEW] = self.create_listview(dic[key])
            if key.lower() == filter_name.FilterQueryName.STORE.value:
                self.optionlist[filter_name.FilterQueryName.STORE] = self.create_store(dic[key])
    
    def create_category(self, value : dict):
        return SearchOptionSetting.create(value, filter_name.FilterQueryName.CATEGORY.value)

    def create_zaiko(self, value :dict):
        return SearchOptionSetting.create(value, filter_name.FilterQueryName.ZAIKO.value)
    
    def create_safesearch(self, value :dict):
        return SearchOptionSetting.create(value, filter_name.FilterQueryName.SAFES.value)
    
    def create_listview(self, value :dict):
        return SearchOptionSetting.create(value, filter_name.FilterQueryName.LISTVIEW.value)
    
    def create_store(self, value :dict):
        return StoreSelectOption.create(value, filter_name.FilterQueryName.STORE.value)
    
class SearchExternalSiteContext(BaseTemplateValue):
    sword :str = ""
    stores :List = []
    categorylist :List = []
    search_results :Union[SearchResult,None] = None
    safes_off_checked :str = ""
    safes_display : bool = True
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
        soss = SearchOptionSettings()
        is_default_setting = len(sfq.setting_list) == 0

        self.categorylist = self.get_category_list(optjson=optjson,
                                                   fq=fq,
                                                   soss=soss,
                                                   isdef=is_default_setting
                                                   )
        self.stores = self.get_store_list(optjson=optjson,
                                          fq=fq,
                                          soss=soss,
                                          isdef=is_default_setting
                                          )

        self.set_safes(sfq=sfq, soss=soss, isdef=is_default_setting)
        self.set_zaiko(sfq=sfq, soss=soss, isdef=is_default_setting)
        self.set_listview(sfq=sfq, soss=soss, isdef=is_default_setting)
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
    
    def set_safes(self,
                  sfq :SearchFilterQuery,
                  soss :SearchOptionSettings,
                  isdef : bool
                  ):
        opt = soss.get_option(filter_name.FilterQueryName.SAFES)
        if opt:
            if not opt.display:
                self.safes_display = False
        if filter_name.FilterQueryName.SAFES in sfq.setting_list\
            and sfq.safes == filter_name.FilterOnOff.OFF:
                self.safes_off_checked = templates_string.HTMLOption.CHECKED.value
        else:
            if not opt or not isdef:
                return
            if not opt.init:
                self.safes_off_checked = templates_string.HTMLOption.CHECKED.value

    
    def set_zaiko(self,
                  sfq :SearchFilterQuery,
                  soss :SearchOptionSettings,
                  isdef : bool
                  ):
        if filter_name.FilterQueryName.ZAIKO in sfq.setting_list\
            and sfq.zaiko == filter_name.FilterOnOff.ON:
            self.zaiko_checked = templates_string.HTMLOption.CHECKED.value
        else:
            if not isdef:
                return
            opt = soss.get_option(filter_name.FilterQueryName.ZAIKO)
            if not opt:
                return
            if opt.init:
                self.zaiko_checked = templates_string.HTMLOption.CHECKED.value

    def set_listview(self,
                     sfq :SearchFilterQuery,
                     soss :SearchOptionSettings,
                     isdef : bool
                     ):
        if filter_name.FilterQueryName.LISTVIEW in sfq.setting_list\
            and sfq.listview == filter_name.FilterOnOff.ON:
            self.listview_checked = templates_string.HTMLOption.CHECKED.value
        else:
            if not isdef:
                return
            opt = soss.get_option(filter_name.FilterQueryName.LISTVIEW)
            if not opt:
                return
            if opt.init:
                self.listview_checked = templates_string.HTMLOption.CHECKED.value


    def get_category_list(self,
                          optjson :Dict,
                          fq :Dict,
                          soss :SearchOptionSettings,
                          isdef :bool
                          ):
        category = optjson['category']['default']
        selected_id :int | None = None
        if filter_name.FilterQueryName.CATEGORY.value in fq:
            selected_id = int(fq[filter_name.FilterQueryName.CATEGORY.value])
        elif isdef:
            selected_id = self.get_category_selected_of_setting(category=category, soss=soss)
        results :list[SearchCategory] = []
        for k, v in category.items():
            scate = SearchCategory(id=int(k), jname=v)
            if selected_id and selected_id == scate.id:
                scate.selected = templates_string.HTMLOption.SELECTED.value
            results.append(scate)
        return results
    
    def get_category_selected_of_setting(self, category :Dict, soss :SearchOptionSettings):
        opt :SearchOptionSetting | None = soss.get_option(filter_name.FilterQueryName.CATEGORY)
        if not opt\
            or len(opt.value) == 0:
            return None
        for k,v in category.items():
            if opt.value == v:
                return int(k)
        return None
    
    def get_store_list(self,
                       optjson :Dict,
                       fq :Dict,
                       soss :SearchOptionSettings,
                       isdef : bool
                       ):
        stores = optjson['store']
        selected_id_list :list[int] | None = None
        if filter_name.FilterQueryName.STORE.value in fq:
            selected_id_list = fq[filter_name.FilterQueryName.STORE.value]
        elif isdef:
            selected_id_list = self.get_store_select_of_setting(stores=stores, soss=soss)
        results :list[SearchStore] = []
        for k, v in stores.items():
            st = SearchStore(store_id=int(k), jname=v["jpname"])
            if selected_id_list and st.store_id in selected_id_list:
                st.checked = templates_string.HTMLOption.CHECKED.value
            results.append(st)
        return results
    
    def get_store_select_of_setting(self, stores :dict, soss :SearchOptionSettings):
        opt : StoreSelectOption | None = soss.get_option(filter_name.FilterQueryName.STORE)
        if not opt:
            return None
        results :list[int] = []
        for k,v in stores.items():
            if opt.is_checked_store(v["jpname"]):
                results.append(int(k))
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
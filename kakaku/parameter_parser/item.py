from typing import Dict, List, Optional
from urllib.parse import  urlencode, parse_qs

from fastapi import Form, Cookie, Depends
from pydantic import BaseModel

from common.filter_name import (
    ActFilterName,
    FilterQueryName,
    ItemSortName,
    FilterOnOff,
    UrlSortName,
    ExtractStoreSortName,
)
from common.templates_string import HTMLOption

from common import const_value
from accessor.item import GroupQuery
from sqlalchemy.orm import Session

from parameter_parser.util import is_suppoer_url, is_valid_id
from parameter_parser.calcitemcomb import (
    ItemCombinationResultForm,
    ItemCombStore,
)

class NewestFilterQuery():
    gid :str = ""
    act :str = ""
    store :str = ""
    isort :str = ""
    zaiko :str = ""
    cfilter_str :str = ""

    is_c_able :bool = False

    def __init__(self,
                 gid :str = "",
                 act :str = "",
                 store :str = "",
                 isort :str = "",
                 zaiko :str = "",
                 cfilter_str :Optional[str] = Cookie(None),
                 ):
        if (not gid 
            and not act
            and not store
            and not isort
            and not zaiko
            ) \
            and cfilter_str:
                self.set_cookie_query(cfilter_str)
        else:
            self.set_query(gid, act, store, isort, zaiko)
        
    def set_query(self,
                  gid :str="",
                  act :str="",
                  store :str="",
                  isort :str="",
                  zaiko :str=""
                  ):
        if is_valid_id(gid):
            self.gid = gid
        if act and act.isdigit() and ActFilterName.hasValue(int(act)):
            self.act = act
        else:
            self.act = str(ActFilterName.ACT.id)
        if store and store.isdigit():
           self.store = store
        if isort and isort.isdigit() and ItemSortName.hasId(int(isort)):
            self.isort = isort
        if zaiko and zaiko.isdigit() and int(zaiko) == FilterOnOff.ON:
            self.zaiko = zaiko
    
    def set_cookie_query(self, cfilter_str:str):
        dic = self.queryToDict(cfilter_str)
        if len(dic) == 0:
            return
        self.set_query(**dic)
        self.is_c_able = True
    
    def is_cookie_available(self) -> bool:
        return self.is_c_able
    
    def is_cookie_update(self):
        if self.is_cookie_available():
            return False
        if not self.cfilter_str is None:
            if self.cfilter_str != urlencode(self.get_qfilter_dict()):
                return True
        return False
    
    def get_filter_dict(self) -> Dict:
        if self.cfilter_str:
            return self.queryToDict(self.cfilter_str)    
        return self.get_qfilter_dict()
    
    def get_cookie(self) -> str:
        return urlencode(self.get_filter_dict())
    
    @staticmethod
    def queryToDict(filter:str) -> Dict:
        pqs = parse_qs(filter)
        results = {}
        for k, v in pqs.items():
            if type(v) is list:
                results[k] = v[0]
            else:
                results[k] = v
        return results

    def get_qfilter_dict(self) -> Dict:
        results = {}
        if self.gid:
            results[FilterQueryName.GID.value] = self.gid
        if self.act:
            results[FilterQueryName.ACT.value] = self.act
        if self.store:
            results[FilterQueryName.STORE.value] = self.store
        if self.isort:
            results[FilterQueryName.ISORT.value] = self.isort
        if self.zaiko:
            results[FilterQueryName.ZAIKO.value] = self.zaiko
        return results

class ItemDetailQuery():
    itemid : str = ""

    def __init__(self, itemid :str = ""):
        if is_valid_id(itemid):
            self.itemid = itemid


class TemplatesItemSort(BaseModel):
    name: str
    id: int
    text: str
    selected: str = ''

def get_item_sort_list(f:Dict) -> List:
    results = [TemplatesItemSort(name=i.qname, id=i.id, text=i.jname) for i in ItemSortName]
    if not FilterQueryName.ISORT.value in f:
        return results         
    for r in results:
        if int(r.id) == int(f[FilterQueryName.ISORT.value]):
            r.selected = HTMLOption.SELECTED.value
    return results

def get_extract_store_sort_list(f:Dict) -> List:
    results = [TemplatesItemSort(name=i.qname, id=i.id, text=i.jname) for i in ExtractStoreSortName]
    if not FilterQueryName.ESSORT.value in f:
        return results         
    for r in results:
        if int(r.id) == int(f[FilterQueryName.ESSORT.value]):
            r.selected = HTMLOption.SELECTED.value
    return results

class TemplatesActStatus(BaseModel):
    id: int
    text: str
    selected: str = ''

def get_actstslist(f:Dict) -> List:
    results = [TemplatesActStatus(id=a.id, text=a.text) for a in ActFilterName]
    if not FilterQueryName.ACT.value in f:
        return results
    for r in results:
        if r.id == int(f[FilterQueryName.ACT.value]):
            r.selected = HTMLOption.SELECTED.value
            break
    return results


class TemplatesGroup(BaseModel):
    group_id: int
    groupname: str = ''
    selected: str = ''

def get_groups(db :Session, f:Dict) -> List:
    results = [TemplatesGroup(group_id=g.group_id, groupname=g.groupname) for g in GroupQuery.get_all(db)]
    if not FilterQueryName.GID.value in f:
        return results
    for r in results:
        if r.group_id == int(f[FilterQueryName.GID.value]):
            r.selected = HTMLOption.SELECTED.value
            break
    return results



class AddItemUrlForm():
    item_name: str = ""
    url_path: str = ""
    search_query :str = ""
    errmsg: str = ""

    def __init__(self
                 ,item_name:Optional[str]=Form(None)
                 ,url_path:Optional[str]=Form(None)
                 ,search_query:Optional[str]=Form(None)
                 ):
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

        if self.item_name:
            return True
        if not self.item_name and not self.url_path:
            self.errmsg = "アイテム名かURLを入力してください"
        return False
    


class AddUrlForm():
    item_id: int = const_value.NONE_ID
    url_path :str = ""
    search_query :str = ""
    errmsg: str = ""

    def __init__(self
                 ,item_id:Optional[str]=Form(None)
                ,url_path:Optional[str]=Form(None)
                ,search_query:Optional[str]=Form(None)
                ):
        if url_path:
            self.url_path = url_path.strip()
        if is_valid_id(item_id):
            self.item_id = int(item_id)
        if search_query:
            self.search_query = search_query

    def is_valid_init(self):
        if self.item_id == const_value.NONE_ID:
            self.errmsg = "アイテムが不明です"
            return False
        return True

    def is_valid(self) -> bool:
        if self.item_id == const_value.NONE_ID:
            self.errmsg = "アイテムが不明です"
            return False
        if self.url_path:
            if is_suppoer_url(self.url_path):
                return True
            else:
                self.errmsg = "対象外のURLです"
                return False
        return False

class UpdateItemNameForm():
    item_id :int = const_value.NONE_ID
    item_name :str = ""
    errmsg: str = ""

    def __init__(self,
                 item_id:Optional[str]=Form(None),
                 item_name:Optional[str]=Form(None)
                 ):
        if is_valid_id(item_id):
            self.item_id = int(item_id)
        
        if item_name:
            self.item_name = item_name
    
    def is_valid_init(self):
        if self.item_id == const_value.NONE_ID:
            self.errmsg = "アイテムが不明です"
            return False
        return True

    def is_valid(self):
        if self.item_id == const_value.NONE_ID:
            self.errmsg = "アイテムが不明です"
            return False
        if not self.item_name \
            or len(self.item_name) == 0:
            self.errmsg = "アイテム名は1文字以上入れて下さい"
            return False
        return True

class ItemIdForm:
    item_id :int = const_value.NONE_ID
    errmsg :str = ""

    def __init__(self,
                 item_id:Optional[str]=Form(None),
                 ):
        if is_valid_id(item_id):
            self.item_id = int(item_id)
    
    def is_valid(self):
        if self.item_id == const_value.NONE_ID:
            self.errmsg = "アイテムが不明です"
            return False
        return True

class ItemIdUrlIdForm:
    item_id :int = const_value.NONE_ID
    url_id :int = const_value.NONE_ID
    errmsg :str = ""

    def __init__(self,
                 item_id:Optional[str]=Form(None),
                 url_id:Optional[str]=Form(None)
                 ):
        if is_valid_id(item_id):
            self.item_id = int(item_id)
        if is_valid_id(url_id):
            self.url_id = int(url_id)
    
    def is_valid(self):
        if self.item_id == const_value.NONE_ID:
            self.errmsg = "アイテムが不明です"
            return False
        if self.url_id == const_value.NONE_ID:
            self.errmsg = "URLが不明です"
            return False
        return True

class InActAllUrlForm(ItemIdForm):
    pass

class InActUrlForm(ItemIdUrlIdForm):
    pass

class ActUrlForm(ItemIdUrlIdForm):
    pass

class UpdateItemUrlForm:
    item_id :int = const_value.NONE_ID
    url_path :str = ""
    errmsg :str = ""

    def __init__(self,
                 item_id:Optional[str]=Form(None),
                 url_path:Optional[str]=Form(None),
                 ):
        if is_valid_id(item_id):
            self.item_id = int(item_id)
        if url_path:
            self.url_path = url_path
    
    def is_valid(self):
        if self.item_id == const_value.NONE_ID:
            self.errmsg = "アイテムが不明です"
            return False
        if self.url_path:
            if is_suppoer_url(self.url_path):
                return True
            else:
                self.errmsg = "対象外のURLです"
                return False
        return False

class UpdateItemAllUrlForm():
    item_id :int = const_value.NONE_ID
    return_user :int = 0
    errmsg :str = ""

    def __init__(self,
                 item_id:Optional[str]=Form(None),
                 return_user:Optional[str]=Form(None),
                 ):
        if is_valid_id(item_id):
            self.item_id = item_id
        if return_user:
            self.return_user = return_user

    def is_valid(self):
        if self.item_id == const_value.NONE_ID:
            self.errmsg = "アイテムが不明です"
            return False
        return True

class RemoveItemUrlForm(ItemIdUrlIdForm):
    pass

class AddGroupForm:
    group_name :str = ""
    errmsg :str = ""

    def __init__(self,
                 group_name:Optional[str]=Form(None),
                 ):
        if group_name:
            self.group_name = group_name
    
    def is_valid(self):
        if self.group_name and len(self.group_name) > 0:
            return True
        return False

class NewestFilterQueryForGroup(NewestFilterQuery):
    pass

class GroupItemUpdateForm():
    group_item_list :List[int] = []
    group_id :int = const_value.NONE_ID

    def __init__(self,
                 group_id :Optional[str] = Form(None),
                 group_item_list :Optional[List[str]]= Form(None),
                 ):
        if is_valid_id(group_id):
            self.group_id = group_id
        if group_item_list:
            results :List[int] = []
            if type(group_item_list) is list:
                for item_id in group_item_list:
                    if is_valid_id(item_id):
                        results.append(int(item_id))
            elif is_valid_id(group_item_list):
                results.append(group_item_list)
            self.group_item_list = results
    
    def is_valid(self):
        if self.group_id == const_value.NONE_ID:
            return False
        return True

class GroupIdForm:
    group_id : int = const_value.NONE_ID

    def __init__(self,
                 group_id :Optional[str] = Form(None),
                 ):
        if is_valid_id(group_id):
            self.group_id = int(group_id)
    
    def is_valid(self):
        if self.group_id == const_value.NONE_ID:
            return False
        return True

class DeleteGroupForm(GroupIdForm):
    pass

class RenameGroupNameInitForm(GroupIdForm):
    pass

class RenameGroupNameForm:
    group_id : int = const_value.NONE_ID
    groupname :str = ""

    def __init__(self,
                 group_id :Optional[str] = Form(None),
                 group_name :Optional[str] = Form(None),
                 ):
        if is_valid_id(group_id):
            self.group_id = int(group_id)
        if group_name and len(group_name) > 0:
            self.groupname = group_name
    
    def is_valid(self):
        if self.group_id == const_value.NONE_ID:
            return False
        if not self.groupname:
            return False
        return True

class DeleteItemForm(ItemIdForm):
    pass

class AnalysisBaseQuery():
    itemid :str = ""
    atid :str = ""

    def __init__(self,
                 itemid :str = "",
                 atid :str = "",
                 ):
        if is_valid_id(itemid):
            self.itemid = itemid
        if is_valid_id(atid):
            self.atid = atid

class UrlListFilterQuery:
    act :str = ""
    usort :str = ""

    def __init__(self,
                 act :str = "",
                 usort :str = "",
                 ):
        if act and act.isdigit() and ActFilterName.hasValue(int(act)):
            self.act = act
        else:
            self.act = str(ActFilterName.ACT.id)
        
        if usort and usort.isdigit() and UrlSortName.hasId(int(usort)):
            self.usort = usort
    
    def get_filter_dict(self) -> dict:
        results = {}
        if self.act:
            results[FilterQueryName.ACT.value] = self.act
        if self.usort:
            results[FilterQueryName.USORT.value] = self.usort
        return results
    
def get_url_sort_list(f:Dict) -> List:
    results = [TemplatesItemSort(name=i.qname, id=i.id, text=i.jname) for i in UrlSortName]
    if not FilterQueryName.USORT.value in f:
        return results         
    for r in results:
        if int(r.id) == int(f[FilterQueryName.USORT.value]):
            r.selected = HTMLOption.SELECTED.value
    return results

class ExtractStoreFilterQuery:
    gid :str = ""
    act :str = ""
    ex_store :str = ""
    essort :str = ""
    zaiko :str = ""

    def __init__(self,
                 gid :str = "",
                 act :str = "",
                 ex_store :str = "",
                 store :str = "",
                 essort :str = "",
                 zaiko :str = ""
                 ):
        
        if is_valid_id(gid):
            self.gid = gid
        if act and act.isdigit() and ActFilterName.hasValue(int(act)):
            self.act = act
        else:
            self.act = str(ActFilterName.ACT.id)
        if ex_store and ex_store.isdigit():
           self.ex_store = ex_store
        if not ex_store and store and store.isdigit():
            self.ex_store = store
        if essort and essort.isdigit() and ExtractStoreSortName.hasId(int(essort)):
            self.essort = essort
        if zaiko and zaiko.isdigit() and int(zaiko) == FilterOnOff.ON:
            self.zaiko = zaiko

    
    def get_filter_dict(self) -> Dict:
        results = {}
        if self.gid:
            results[FilterQueryName.GID.value] = self.gid
        if self.act:
            results[FilterQueryName.ACT.value] = self.act
        if self.ex_store:
            results[FilterQueryName.EX_STORE.value] = self.ex_store
        if self.essort:
            results[FilterQueryName.ESSORT.value] = self.essort
        if self.zaiko:
            results[FilterQueryName.ZAIKO.value] = self.zaiko
        return results

def get_in_stock_filter_checked(f :dict) -> str:
    if FilterQueryName.ZAIKO.value in f\
        and int(f[FilterQueryName.ZAIKO.value]) == FilterOnOff.ON:
        return HTMLOption.CHECKED.value
    return ""

class EditShippingConditionForm:
    errmsg :str = ""
    store_list :List[ItemCombStore] = []

    def __init__(self,
                 ):
        pass
    
    def set_store_list(self, stores):
        if stores:
            self.store_list = ItemCombinationResultForm.parse_stores(stores=stores)

class DeleteStoreForm:
    store_id :int = const_value.NONE_ID
    errmsg :str = ""

    def __init__(self,
                 store_id :Optional[str] = Form(None),
                 ):
        if is_valid_id(store_id):
            self.store_id = store_id
    
    def is_valid(self):
        if self.store_id == const_value.NONE_ID:
            self.errmsg = "店舗が不明です"
            return False
        return True
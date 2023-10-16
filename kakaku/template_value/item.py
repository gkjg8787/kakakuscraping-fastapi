from typing import List, Dict, Optional

from fastapi import Request
from pydantic import BaseModel

from sqlalchemy.orm import Session

from common import (
    filter_name,
    const_value,
    templates_string,
)
from accessor.item import (
    NewestQuery,
    ItemQuery,
    UrlQuery,
    UrlActive,
    GroupQuery,
)
import parameter_parser.item as ppi
import parameter_parser.store as pps

from proc.scrapingmanage import sendTask
from proc.sendcmd import ScrOrder

from proc import get_sys_status, system_status

from analysis import database_analysis

from accessor.util import sqlalchemy_result_all_to_dict_list


def is_update_process_alive(db :Session):
    syssts = get_sys_status.getSystemStatus(db)
    if syssts == system_status.SystemStatus.FAULT.name \
        or syssts == system_status.SystemStatus.STOP.name \
        or syssts == system_status.SystemStatus.NONE.name:
        return False
    return True

class BaseTemplateValue(BaseModel):
    request: Request = None
    class Config:
        arbitrary_types_allowed = True

class NewestItemList(BaseTemplateValue):
    topscrollid: str
    res : List
    res_length: int = 0
    actstslist: List
    itemSortList: List
    groups: List
    storelist: List
    fquery: Dict
    ZAIKO_CHECKED : str = ""
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value
    ITEMACT_NAME: str =  filter_name.FilterQueryName.ACT.value
    ITEMSORT_NAME: str = filter_name.FilterQueryName.ISORT.value
    EQST_NAME: str = filter_name.FilterQueryName.STORE.value
    ITEMID_Q_NAME : str = filter_name.ItemDetailQueryName.ITEMID.value
    POST_ITEM_ID : str = filter_name.TemplatePostName.ITEM_ID.value
    POST_GROUP_ID :str = filter_name.TemplatePostName.GROUP_ID.value
    POST_ITEM_ALL_UPDATE :str = filter_name.TemplatePostName.ITEM_ALL_UPDATE.value
    item_all_update_value :str = filter_name.ItemUpdateValue.ITEM_ALL_UPDATE
    POST_RETURN_USER :str = filter_name.TemplatePostName.RETURN_USER.value
    return_user :str = filter_name.FilterOnOff.ON
    STOCK_NAME :str = filter_name.FilterQueryName.ZAIKO.value
    STOCK_VALUE :int = filter_name.FilterOnOff.ON

    def __init__(self, request, nfq :ppi.NewestFilterQuery, db :Session):
        fd = nfq.get_filter_dict()
        super().__init__(
                topscrollid=""
                ,request=request
                ,res=NewestQuery.get_newest_data(db, filter=fd)
                ,actstslist = ppi.get_actstslist(fd)
                ,itemSortList = ppi.get_item_sort_list(fd)
                ,groups = ppi.get_groups(db, f=fd)
                ,storelist = []
                ,fquery=fd
                ,ZAIKO_CHECKED=ppi.get_in_stock_filter_checked(fd)
                )
        
        self.res_length = len(self.res)
        self.storelist = pps.get_stores_for_newest(db, filter=self.fquery)
    
        if filter_name.FilterQueryName.GID.value in self.fquery:
            gid = int(self.fquery[filter_name.FilterQueryName.GID.value])
            def get_exist_gid(gid):
                for g in self.groups:
                    if g.group_id == gid:
                        return gid
                return filter_name.FilterDefault.GID
            
            self.fquery[filter_name.FilterQueryName.GID.value] = get_exist_gid(gid)

class UpdateAllItemUrlPostContext(BaseTemplateValue):
    updateSuccess :bool = False
    return_user :bool = True
    errmsg :str = ""

    def __init__(self, request, db :Session):
        super().__init__(request=request)
        if not is_update_process_alive(db):
            self.errmsg = "更新できない状態です。サーバを確認して下さい。"
            return
        self.update_all_data()    
    
    def update_all_data(self):
        sendTask(ScrOrder.UPDATE_ACT_ALL, '', '')
        self.updateSuccess = True
    
    

class ItemDetailContext(BaseTemplateValue):
    loglist : List
    loglist_length : int = 0
    items : Dict
    urllist : List
    ITEMID_Q_NAME : str = filter_name.ItemDetailQueryName.ITEMID.value
    item_data_years_limit :int = filter_name.ItemDetailConst.YEARS_LIMIT.value
    item_data_max_cnt :int = filter_name.ItemDetailConst.MAX_LIMIT.value
    POST_ITEM_ID : str = filter_name.TemplatePostName.ITEM_ID.value
    POST_URL_ID :str = filter_name.TemplatePostName.URL_ID.value
    POST_URL_PATH :str = filter_name.TemplatePostName.URL_PATH.value
    ACTIVE_VALUE :str = UrlActive.ACTIVE.value
    SEARCH_WORD_NAME :str = filter_name.FilterQueryName.WORD.value

    def __init__(self, request, idq :ppi.ItemDetailQuery, db :Session):
        super().__init__(
            request = request,
            loglist = [],
            items = {},
            urllist = [],
        )
        if not idq.itemid:
            return
        itemid = int(idq.itemid)
        self.items = NewestQuery.get_newest_data_by_item_id(db, item_id=itemid)
        if not self.items:
            return
        self.loglist = ItemQuery.get_item_pricelog_by_item_id_1year(db,
                                                                    item_id=itemid,
                                                                    result_limit=self.item_data_max_cnt,
                                                                    )
        if self.loglist:
            self.loglist_length = len(self.loglist)
        self.urllist = UrlQuery.get_urlinfo_by_item_id(db, item_id=itemid)

    def has_data(self) -> bool:
        if not self.items or len(self.items) == 0:
            return False
        return True

class ItemDetailChartContext(BaseTemplateValue):
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value
    upjp :List
    npjp :List
    item_id : int = const_value.NONE_ID

    def __init__(self, request, idq :ppi.ItemDetailQuery, db :Session):
        super().__init__(
            request=request,
            upjp = [],
            npjp = [],
        )
        if not idq.itemid:
            return
        self.item_id = int(idq.itemid)
        self.upjp = self.__get_used_point_data(db, self.item_id)
        self.npjp = self.__get_new_point_data(db, self.item_id)
    
    def has_data(self):
        if self.item_id == const_value.NONE_ID:
            return False
        if len(self.upjp) == 0 and len(self.npjp) == 0:
            return False
        return True
    
    def __get_used_point_data(self, db :Session, item_id :int):
        u = ItemQuery.get_daily_min_used_pricelog_by_item_id_and_since_year_ago(
            db=db,
            item_id=item_id,
            year=filter_name.ItemDetailConst.YEARS_LIMIT.value,
        )
        up = self.__get_pricelist_of_uniq_point_data(u)
        results = [{'x':p['created_at'], 'y':p['price']} for p in up]
        #upj = json.dumps(results)
        #return upj
        return results
    
    def __get_new_point_data(self, db :Session, item_id :int):
        n = ItemQuery.get_daily_min_new_pricelog_by_item_id_and_since_year_ago(
            db=db,
            item_id=item_id,
            year=filter_name.ItemDetailConst.YEARS_LIMIT.value,
        )
        np = self.__get_pricelist_of_uniq_point_data(n)
        results = [{"x":p["created_at"], "y":p["price"]} for p in np]
        #npj = json.dumps(results)
        #return npj
        return results

    @staticmethod
    def __get_pricelist_of_uniq_point_data(pl :List) -> List:
        initflg = True
        results = []
        for d in pl:
            dic = {}
            for k,v in d._mapping.items():
                dic[k] = v
            if initflg:
                initflg = False
                preprice = dic['price']
                prev = d
                results = [dic]
                isContinue = False
                continue
            if preprice == dic['price']:
                prev = dic
                isContinue = True
                continue
            if isContinue \
                and prev['price'] == preprice:
                results.append(prev)
            isContinue = False
            preprice = dic['price']
            prev = dic
            results.append(dic)
        return results


class AddItemUrlPostContext(BaseTemplateValue):
    itemName : str = ""
    urlPath :str = ""
    addSuccess :bool = False
    errmsg :str = ""
    search_query :Optional[str] = None
    POST_ITEM_NAME :str = filter_name.TemplatePostName.ITEM_NAME.value
    POST_URL_PATH :str = filter_name.TemplatePostName.URL_PATH.value

    def __init__(self, request,
                 adduform :ppi.AddItemUrlForm,
                 db :Session
                 ):
        super().__init__(
            request=request,
            itemName=adduform.item_name,
            urlPath=adduform.url_path,
        )
        if not adduform.is_valid():
            self.errmsg = adduform.errmsg
            return
        if adduform.search_query:
            self.search_query = adduform.search_query
        self.add_data(db)
        
            
    def add_data(self, db :Session):
        NewestQuery.add_item(item_name=self.itemName,
                             url_path=self.urlPath,
                             db=db)
        self.addSuccess = True

class AddUrlInitContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    errmsg :str = ""
    POST_ITEM_ID :str = filter_name.TemplatePostName.ITEM_ID.value
    POST_URL_PATH :str = filter_name.TemplatePostName.URL_PATH.value
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, adduform :ppi.AddUrlForm):
        super().__init__(
            request=request,
        )
        if not adduform.is_valid_init():
            self.errmsg = adduform.errmsg
            return
        self.item_id = adduform.item_id
        
            

class AddUrlPostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    urlPath :str = ""
    addSuccess :bool = False
    search_query :Optional[str] = None
    errmsg :str = ""
    POST_ITEM_ID :str = filter_name.TemplatePostName.ITEM_ID.value
    POST_URL_PATH :str = filter_name.TemplatePostName.URL_PATH.value
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, adduform :ppi.AddUrlForm, db :Session):
        super().__init__(
            request=request,
            urlPath=adduform.url_path,
        )
        if adduform.item_id != const_value.NONE_ID:
            self.item_id = adduform.item_id
            item = ItemQuery.get_item(db, item_id=self.item_id)
            if not item:
                self.errmsg = "アイテムが見つかりません"
                return
        if not adduform.is_valid():
            self.errmsg = adduform.errmsg
            return
        if adduform.search_query:
            self.search_query = adduform.search_query
        self.add_data(db)

            
    
    def add_data(self, db :Session):
        UrlQuery.add_url_and_urlinitem(db, item_id=self.item_id, urlpath=self.urlPath)
        self.addSuccess = True

class UpdateItemNameInitContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    errmsg :str = ""
    pre_item_name :str = ""
    POST_ITEM_ID :str = filter_name.TemplatePostName.ITEM_ID.value
    POST_ITEM_NAME :str = filter_name.TemplatePostName.ITEM_NAME.value
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, upnameform :ppi.UpdateItemNameForm, db :Session):
        super().__init__(
            request=request,
        )
        if upnameform.is_valid_init():
            self.item_id = upnameform.item_id
            item = ItemQuery.get_item(db, item_id=self.item_id)
            if item:
                self.pre_item_name = item.name
            else:
                self.errmsg = "アイテムが見つかりません"
        else:
            self.errmsg = upnameform.errmsg


class UpdateItemNamePostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    item_name :str = ""
    updateSuccess :bool = False
    errmsg :str = ""
    pre_item_name :str = ""
    POST_ITEM_ID :str = filter_name.TemplatePostName.ITEM_ID.value
    POST_ITEM_NAME :str = filter_name.TemplatePostName.ITEM_NAME.value
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, upnameform :ppi.UpdateItemNameForm, db :Session):
        super().__init__(
            request=request,
        )
        if upnameform.is_valid():
            self.item_name = upnameform.item_name
            self.item_id = upnameform.item_id
            self.update_data(db)
        else:
            self.errmsg = upnameform.errmsg
            if upnameform.item_id != const_value.NONE_ID:
                self.item_id = upnameform.item_id
                item = ItemQuery.get_item(db, item_id=self.item_id)
                if item:
                    self.pre_item_name = item.name
                else:
                    self.errmsg += ", アイテムが見つかりません"


            
    def update_data(self, db :Session):
        ItemQuery.update_items_name_by_item_id(db, item_id=self.item_id,name=self.item_name)
        self.updateSuccess = True

class InActAllUrlPostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    updateSuccess :bool = False
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, inactform :ppi.InActAllUrlForm, db :Session):
        super().__init__(
            request=request,
        )
        if inactform.is_valid():
            self.item_id = inactform.item_id
            self.inact_all_url(db)
        else:
            self.errmsg = inactform.errmsg

    def inact_all_url(self, db :Session):
        UrlQuery.update_url_active_all_by_item_id(db, item_id=self.item_id, isactive=UrlActive.INACTIVE)
        self.updateSuccess = True

class InActUrlPostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    url_id :int = const_value.NONE_ID
    updateSuccess :bool = False
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, inactform :ppi.InActUrlForm, db :Session):
        super().__init__(request=request)
        if inactform.is_valid():
            self.item_id = inactform.item_id
            self.url_id = inactform.url_id
            self.inact_url(db)
        else:
            self.errmsg = inactform.errmsg
            if inactform.item_id:
                self.item_id = inactform.item_id
            if inactform.url_id:
                self.url_id = inactform.url_id
    
    def inact_url(self, db :Session):
        UrlQuery.update_url_active(db,
                                   item_id=self.item_id,
                                   url_id=self.url_id,
                                   isactive=UrlActive.INACTIVE)
        self.updateSuccess = True

class ActUrlPostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    url_id :int = const_value.NONE_ID
    updateSuccess :bool = False
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, actform :ppi.ActUrlForm, db :Session):
        super().__init__(request=request)
        if actform.is_valid():
            self.item_id = actform.item_id
            self.url_id = actform.url_id
            self.act_url(db)
        else:
            self.errmsg = actform.errmsg
            if actform.item_id:
                self.item_id = actform.item_id
            if actform.url_id:
                self.url_id = actform.url_id
    
    def act_url(self, db :Session):
        UrlQuery.update_url_active(db,
                                   item_id=self.item_id,
                                   url_id=self.url_id,
                                   isactive=UrlActive.ACTIVE)
        self.updateSuccess = True

class UpdateItemUrlPostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    updateSuccess :bool = False
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, upurlform :ppi.UpdateItemUrlForm, db :Session):
        super().__init__(request=request)
        if upurlform.item_id:
            self.item_id = upurlform.item_id
        if not is_update_process_alive(db):
            self.errmsg = "更新できない状態です。サーバを確認して下さい。"
            return
        if upurlform.is_valid():
            self.update_data(upurlform.url_path)
        else:
            self.errmsg = upurlform.errmsg
            
    
    def update_data(self, url_path):
        sendTask(ScrOrder.UPDATE, url_path, str(const_value.NONE_ID))
        self.updateSuccess = True

class UpdateItemAllUrlPostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    updateSuccess :bool = False
    return_user :bool = False
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, upurlform :ppi.UpdateItemAllUrlForm, db :Session):
        super().__init__(request=request)
        if upurlform.return_user:
            self.return_user = True
        if upurlform.item_id:
            self.item_id = upurlform.item_id
        if not is_update_process_alive(db):
            self.errmsg = "更新できない状態です。サーバを確認して下さい。"
            return
        if upurlform.is_valid():
            self.update_data(db)
        else:
            self.errmsg = upurlform.errmsg
            
    
    def update_data(self, db :Session):
        urlinitems = UrlQuery.get_act_urlinfo_by_item_id(db, item_id=self.item_id)
        for uii in urlinitems:
            sendTask(ScrOrder.UPDATE, uii.urlpath, str(const_value.NONE_ID))
        self.updateSuccess = True

class RemoveItemUrlPostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    updateSuccess :bool = False
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, remurlform :ppi.RemoveItemUrlForm, db :Session):
        super().__init__(request=request)
        if remurlform.is_valid():
            self.item_id = remurlform.item_id
            self.remove_data(db, url_id=remurlform.url_id)
        else:
            self.errmsg = remurlform.errmsg
            if remurlform.item_id:
                self.item_id = remurlform.item_id
    
    def remove_data(self, db :Session, url_id:int):
        UrlQuery.delete_urlinitem(db, item_id=self.item_id, url_id=url_id)
        self.updateSuccess = True

class AddGroupPostContext(BaseTemplateValue):
    group_name :str = ""
    group_id :int = const_value.NONE_ID
    errmsg :str = ""
    addSuccess :bool = False
    POST_GROUP_NAME :str = filter_name.TemplatePostName.GROUP_NAME.value
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value

    def __init__(self, request, addgform :ppi.AddGroupForm, db :Session):
        super().__init__(request=request)
        if addgform.is_valid():
            self.group_name = addgform.group_name
            self.add_group(db)
            return
        else:
            self.errmsg = addgform.errmsg
            if addgform.group_name:
                self.group_name = addgform.group_name
    
    def add_group(self, db :Session):
        if not GroupQuery.get_group_by_name(db, name=self.group_name):
            group_id = GroupQuery.add_group(db, self.group_name)
            if group_id and group_id > const_value.NONE_ID:
                self.group_id = group_id
                self.addSuccess = True
                return
            else:
                self.errmsg = "グループ追加に失敗しました"
                return
        else:
            self.errmsg = "グループ名は既に存在しています"

class EditGroupContext(BaseTemplateValue):
    gfid : int = filter_name.FilterDefault.GID
    res : List = []
    groups: List
    actstslist: List
    itemSortList: List
    fquery: Dict
    ZAIKO_CHECKED : str = ""
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value
    ITEMACT_NAME: str =  filter_name.FilterQueryName.ACT.value    
    ITEMSORT_NAME: str = filter_name.FilterQueryName.ISORT.value
    POST_GROUP_ID : str = filter_name.TemplatePostName.GROUP_ID.value
    POST_GROUP_ITEM_LIST : str = filter_name.TemplatePostName.GROUP_ITEM_LIST.value
    STOCK_NAME :str = filter_name.FilterQueryName.ZAIKO.value
    STOCK_VALUE :int = filter_name.FilterOnOff.ON

    def __init__(self, request, nfqg :ppi.NewestFilterQueryForGroup, db :Session):
        fd = nfqg.get_filter_dict()
        super().__init__(
                request=request
                ,actstslist = ppi.get_actstslist(fd)
                ,itemSortList = ppi.get_item_sort_list(fd)
                ,groups = ppi.get_groups(db, f=fd)
                ,fquery=fd
                ,ZAIKO_CHECKED=ppi.get_in_stock_filter_checked(fd)
                )
    
        if filter_name.FilterQueryName.GID.value in self.fquery:
            gid = int(self.fquery[filter_name.FilterQueryName.GID.value])
            def get_exist_gid(gid):
                for g in self.groups:
                    if g.group_id == gid:
                        return gid
                return filter_name.FilterDefault.GID
            
            self.fquery[filter_name.FilterQueryName.GID.value] = get_exist_gid(gid)
            self.gfid = self.fquery[filter_name.FilterQueryName.GID.value]
            newest_list = NewestQuery.get_newest_data_for_edit_group(db, filter=fd)
            self.res = self.get_newest_list_add_seleted(db, newest_list=newest_list, group_id=self.gfid)

    def get_newest_list_add_seleted(self, db :Session, newest_list, group_id :int):
        gi_list = GroupQuery.get_group_item_by_group_id(db, group_id=group_id)
        group_item_id_list = [gi.item_id for gi in gi_list]
        results = []
        for row in newest_list:
            dic = {}
            for k,v in row._mapping.items():
                dic[k] = v
                if 'item_id' == k and v in group_item_id_list:
                    dic[templates_string.HTMLOption.CHECKED.value] = templates_string.HTMLOption.CHECKED.value
            results.append(dic)
        return results

class UpdateGroupItem():
    group_id :int = const_value.NONE_ID
    def __init__(self, giform :ppi.GroupItemUpdateForm, db :Session):
        if giform.is_valid():
            self.group_id = giform.group_id
            self.update_group_item(db, giform.group_item_list)
    
    def update_group_item(self, db :Session, group_item_list):
        GroupQuery.update_group_item(db, group_id=self.group_id, item_list=group_item_list)


    def get_query(self):
        if self.group_id and self.group_id != const_value.NONE_ID:
            return f"?{filter_name.FilterQueryName.GID.value}={self.group_id}"
        return ""

class DeleteGroupInitContext(BaseTemplateValue):
    gid :int = const_value.NONE_ID
    groupname :str = ""
    POST_GROUP_ID :str = filter_name.TemplatePostName.GROUP_ID.value
    GROUPID_NAME :str = filter_name.FilterQueryName.GID.value

    def __init__(self, request, delgform :ppi.DeleteGroupForm, db :Session):
        super().__init__(request=request)
        if delgform.is_valid():
            self.gid = delgform.group_id
            g = GroupQuery.get_group_by_group_id(db, gid=self.gid)
            self.groupname = g.groupname

class DeleteGroupContext(DeleteGroupInitContext):
    errmsg :str = ""
    delSuccess :bool = False

    def __init__(self, request, delgform :ppi.DeleteGroupForm, db :Session):
        super().__init__(request=request, delgform=delgform, db=db)
        if delgform.is_valid():
            self.delete_group(db)
            
    def delete_group(self, db :Session):
        GroupQuery.del_group(db, group_id=self.gid)
        self.delSuccess = True

class RenameGroupNameInitContext(BaseTemplateValue):
    gid :int = const_value.NONE_ID
    before_groupname :str = ""
    POST_GROUP_ID :str = filter_name.TemplatePostName.GROUP_ID.value
    POST_GROUP_NAME :str = filter_name.TemplatePostName.GROUP_NAME.value
    GROUPID_NAME :str = filter_name.FilterQueryName.GID.value

    def __init__(self, request, rgnform :ppi.RenameGroupNameInitForm, db :Session):
        super().__init__(request=request)
        if rgnform.is_valid():
            self.gid = rgnform.group_id
            g = GroupQuery.get_group_by_group_id(db, gid=self.gid)
            self.before_groupname = g.groupname

class RenameGroupNameContext(BaseTemplateValue):
    gid :int = const_value.NONE_ID
    groupname :str = ""
    updateSuccess :bool = False
    POST_GROUP_ID :str = filter_name.TemplatePostName.GROUP_ID.value
    POST_GROUP_NAME :str = filter_name.TemplatePostName.GROUP_NAME.value
    GROUPID_NAME :str = filter_name.FilterQueryName.GID.value

    def __init__(self, request, rgnform :ppi.RenameGroupNameForm, db :Session):
        super().__init__(request=request)
        if rgnform.is_valid():
            self.gid = rgnform.group_id
            self.groupname = rgnform.groupname
            self.rename_group(db)
    
    def rename_group(self, db :Session):
        GroupQuery.update_group_name(db, group_id=self.gid, name=self.groupname)
        self.updateSuccess = True

class DeleteItemInitContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    itemname :str = ""
    POST_ITEM_ID :str = filter_name.TemplatePostName.ITEM_ID.value
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, diform :ppi.DeleteItemForm, db :Session):
        super().__init__(request=request)
        if diform.is_valid():
            self.item_id = diform.item_id
            self.itemname = ItemQuery.get_item(db, item_id=self.item_id).name
        else:
            self.errmsg = diform.errmsg

class DeleteItemContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    itemname :str = ""
    POST_ITEM_ID :str = filter_name.TemplatePostName.ITEM_ID.value
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value
    delSuccess :bool = False

    def __init__(self, request, diform :ppi.DeleteItemForm, db :Session):
        super().__init__(request=request)
        if not diform.is_valid():
            self.errmsg = diform.errmsg
            return
        self.item_id = diform.item_id
        self.itemname = ItemQuery.get_item(db, item_id=self.item_id).name
        self.delete_data(db)

    def delete_data(self, db :Session):
        ItemQuery.delete_item_relation_by_item_id(db, item_id=self.item_id)
        self.delSuccess = True

class ItemAnalysisPeriod:
    id :int
    selected :str = ""
    text :str

    def __init__(self, id :int, text :str):
        self.id = id
        self.text = text

class ItemAnalysisContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    analysis_term_id :int = filter_name.AnalysisTermName.ONE_WEEK.id

    period_start :str = ""
    period_end :str = ""

    item_count : database_analysis.CountResult = None
    url_count :database_analysis.CountResult = None

    item_price :database_analysis.PriceResult = None

    url_download :database_analysis.UrlDownLoadResult = None

    store_count :database_analysis.CountResult = None

    store_most_common :database_analysis.StoreMostCommonResult = None

    url_store_count_average :database_analysis.UrlStoreCountAverageResult = None

    analysisPeriodList :list[ItemAnalysisPeriod] = []

    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value
    ANALYSIS_Q_NAME :str = filter_name.AnalysisQueryName.ATID.value

    errmsg :str = ""

    def __init__(self, request, anaq :ppi.AnalysisBaseQuery, db :Session):
        super().__init__(request=request)

        if anaq.itemid:
            self.item_id = int(anaq.itemid)
        if anaq.atid:
            self.analysis_term_id = int(anaq.atid)
        
        self.analysisPeriodList = self.create_analysis_period_list(self.analysis_term_id)

        result = database_analysis.get_log_analysis(db=db, atid=self.analysis_term_id)
        if result.is_error():
            self.errmsg = result.get_error().value
            return
        
        self.period_start = result.get_start_datetime().date()
        self.period_end = result.get_end_datetime().date()

        self.item_count = result.get_item_count()
        self.url_count = result.get_url_count()

        self.item_price = result.get_item_price()

        self.url_download = result.get_url_download()

        self.store_count = result.get_store_count()

        STORE_RANKING_MAX = 5
        self.store_most_common = result.get_store_most_common(max_store_num=STORE_RANKING_MAX)

        self.url_store_count_average = result.get_url_store_count_average()

        
    
    @staticmethod
    def create_analysis_period_list(analysis_term_id :int):
        analysisPeriodList = []
        for atn in filter_name.AnalysisTermName:
            iap = ItemAnalysisPeriod(id=atn.id, text=atn.jname)
            if analysis_term_id == atn.id:
                iap.selected = templates_string.HTMLOption.SELECTED.value
            analysisPeriodList.append(iap)
        return analysisPeriodList
        
class UrlListContext(BaseTemplateValue):
    res : list
    res_length :int = 0
    ITEMACT_NAME :str = filter_name.FilterQueryName.ACT.value
    actstslist :list
    fquery :dict

    URLSORT_NAME :str = filter_name.FilterQueryName.USORT.value
    urlSortList :list

    def __init__(self, request, db :Session, ufq :ppi.UrlListFilterQuery):
        fd = ufq.get_filter_dict()
        super().__init__(request=request
                         ,res=UrlQuery.get_url_and_item_comb_list(db,filter=fd)
                         ,actstslist = ppi.get_actstslist(fd)
                         ,fquery=fd
                         ,urlSortList = ppi.get_url_sort_list(fd)
                         )
        self.res_length = len(self.res)

class ExtractStoreItemListContext(BaseTemplateValue):
    res : List
    res_length: int = 0
    actstslist: List
    esSortList :List
    groups: List
    storelist: List
    fquery: Dict
    ZAIKO_CHECKED : str = ""
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value
    ITEMACT_NAME: str =  filter_name.FilterQueryName.ACT.value
    EXST_NAME: str = filter_name.FilterQueryName.EX_STORE.value
    ITEMID_Q_NAME : str = filter_name.ItemDetailQueryName.ITEMID.value
    ESSORT_NAME: str = filter_name.FilterQueryName.ESSORT.value
    POST_ITEM_ID : str = filter_name.TemplatePostName.ITEM_ID.value
    POST_GROUP_ID :str = filter_name.TemplatePostName.GROUP_ID.value
    POST_ITEM_ALL_UPDATE :str = filter_name.TemplatePostName.ITEM_ALL_UPDATE.value
    item_all_update_value :str = filter_name.ItemUpdateValue.ITEM_ALL_UPDATE
    POST_RETURN_USER :str = filter_name.TemplatePostName.RETURN_USER.value
    return_user :str = filter_name.FilterOnOff.ON
    STOCK_NAME :str = filter_name.FilterQueryName.ZAIKO.value
    STOCK_VALUE :int = filter_name.FilterOnOff.ON

    def __init__(self, request, esfq :ppi.ExtractStoreFilterQuery, db :Session):
        fd = esfq.get_filter_dict()
        super().__init__(
                request=request
                ,res=self.get_extract_storename_newest_data(db, filter=fd)
                ,actstslist = ppi.get_actstslist(fd)
                ,esSortList = ppi.get_extract_store_sort_list(fd)
                ,groups = ppi.get_groups(db, f=fd)
                ,storelist = []
                ,fquery=fd
                ,ZAIKO_CHECKED=ppi.get_in_stock_filter_checked(fd)
                )
        
        self.res_length = len(self.res)
        self.storelist = pps.get_stores_for_extract_store(db, filter=self.fquery)
    
        if filter_name.FilterQueryName.GID.value in self.fquery:
            gid = int(self.fquery[filter_name.FilterQueryName.GID.value])
            def get_exist_gid(gid):
                for g in self.groups:
                    if g.group_id == gid:
                        return gid
                return filter_name.FilterDefault.GID
            
            self.fquery[filter_name.FilterQueryName.GID.value] = get_exist_gid(gid)

    @staticmethod
    def get_extract_storename_newest_data(db :Session, filter :dict):
        results = []
        db_res = NewestQuery.get_storename_newest_data(db, filter=filter)
        item_grp = {}
        for row in db_res:
            dic = dict(row._mapping.items())
            if dic["item_id"] in item_grp:
                item_grp[dic["item_id"]].append(dic)
            else:
                item_grp[dic["item_id"]] = [dic]

        for item_list in item_grp.values():
            lowest = None
            for item in item_list:
                if not lowest:
                    lowest = item
                    continue
                if item["price"] < lowest["price"]:
                    lowest = item
                    continue
            if lowest:
                results.append(lowest)
        return results
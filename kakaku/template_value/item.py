from typing import List, Dict, Optional

from fastapi import Request
from pydantic import BaseModel

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

def is_update_process_alive():
    syssts = get_sys_status.getSystemStatus()
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

    def __init__(self, request, nfq :ppi.NewestFilterQuery):
        fd = nfq.get_filter_dict()
        super().__init__(
                topscrollid=""
                ,request=request
                ,res=NewestQuery.get_newest_data(fd)
                ,actstslist = ppi.get_actstslist(fd)
                ,itemSortList = ppi.get_item_sort_list(fd)
                ,groups = ppi.get_groups(fd)
                ,storelist = []
                ,fquery=fd
                )
        
        self.res_length = len(self.res)
        self.storelist = pps.get_stores_for_newest(filter=self.fquery)
    
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

    def __init__(self, request):
        super().__init__(request=request)
        if not is_update_process_alive():
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

    def __init__(self, request, idq :ppi.ItemDetailQuery):
        super().__init__(
            request = request,
            loglist = [],
            items = {},
            urllist = [],
        )
        if not idq.itemid:
            return
        itemid = int(idq.itemid)
        self.items = NewestQuery.get_newest_data_by_item_id(itemid)
        if not self.items:
            return
        self.loglist = ItemQuery.get_item_pricelog_by_item_id_1year(item_id=itemid,
                                                              result_limit=self.item_data_max_cnt,
                                                              )
        if self.loglist:
            self.loglist_length = len(self.loglist)
        self.urllist = UrlQuery.get_urlinfo_by_item_id(itemid)

    def has_data(self) -> bool:
        if not self.items or len(self.items) == 0:
            return False
        return True

class ItemDetailChartContext(BaseTemplateValue):
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value
    upjp :List
    npjp :List
    item_id : int = const_value.NONE_ID

    def __init__(self, request, idq :ppi.ItemDetailQuery):
        super().__init__(
            request=request,
            upjp = [],
            npjp = [],
        )
        if not idq.itemid:
            return
        self.item_id = int(idq.itemid)
        self.upjp = self.__get_used_point_data(self.item_id)
        self.npjp = self.__get_new_point_data(self.item_id)
    
    def has_data(self):
        if self.item_id == const_value.NONE_ID:
            return False
        if len(self.upjp) == 0 and len(self.npjp) == 0:
            return False
        return True
    
    def __get_used_point_data(self, item_id :int):
        u = ItemQuery.get_daily_min_used_pricelog_by_item_id_and_since_year_ago(
            item_id=item_id,
            year=filter_name.ItemDetailConst.YEARS_LIMIT.value,
        )
        up = self.__get_pricelist_of_uniq_point_data(u)
        results = [{'x':p['created_at'], 'y':p['price']} for p in up]
        #upj = json.dumps(results)
        #return upj
        return results
    
    def __get_new_point_data(self, item_id :int):
        n = ItemQuery.get_daily_min_new_pricelog_by_item_id_and_since_year_ago(
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

    def __init__(self, request, adduform :ppi.AddItemUrlForm):
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
        self.add_data()
        
            
    def add_data(self):
        NewestQuery.add_item(item_name=self.itemName, url_path=self.urlPath)
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

    def __init__(self, request, adduform :ppi.AddUrlForm):
        super().__init__(
            request=request,
            urlPath=adduform.url_path,
        )
        if adduform.item_id != const_value.NONE_ID:
            self.item_id = adduform.item_id
        if not adduform.is_valid():
            self.errmsg = adduform.errmsg
            return
        if adduform.search_query:
            self.search_query = adduform.search_query
        self.add_data()

            
    
    def add_data(self):
        UrlQuery.add_url_and_urlinitem(item_id=self.item_id, urlpath=self.urlPath)
        self.addSuccess = True

class UpdateItemNameInitContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    errmsg :str = ""
    pre_item_name :str = ""
    POST_ITEM_ID :str = filter_name.TemplatePostName.ITEM_ID.value
    POST_ITEM_NAME :str = filter_name.TemplatePostName.ITEM_NAME.value
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, upnameform :ppi.UpdateItemNameForm):
        super().__init__(
            request=request,
        )
        if upnameform.is_valid_init():
            self.item_id = upnameform.item_id
            item = ItemQuery.get_item(self.item_id)
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

    def __init__(self, request, upnameform :ppi.UpdateItemNameForm):
        super().__init__(
            request=request,
        )
        if upnameform.is_valid():
            self.item_name = upnameform.item_name
            self.item_id = upnameform.item_id
            self.update_data()
        else:
            self.errmsg = upnameform.errmsg
            if upnameform.item_id != const_value.NONE_ID:
                self.item_id = upnameform.item_id
                item = ItemQuery.get_item(self.item_id)
                if item:
                    self.pre_item_name = item.name
                else:
                    self.errmsg += ", アイテムが見つかりません"


            
    def update_data(self):
        ItemQuery.update_items_name_by_item_id(item_id=self.item_id,name=self.item_name)
        self.updateSuccess = True

class InActAllUrlPostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    updateSuccess :bool = False
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, inactform :ppi.InActAllUrlForm):
        super().__init__(
            request=request,
        )
        if inactform.is_valid():
            self.item_id = inactform.item_id
            self.inact_all_url()
        else:
            self.errmsg = inactform.errmsg

    def inact_all_url(self):
        UrlQuery.update_url_active_all_by_item_id(item_id=self.item_id, isactive=UrlActive.INACTIVE)
        self.updateSuccess = True

class InActUrlPostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    url_id :int = const_value.NONE_ID
    updateSuccess :bool = False
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, inactform :ppi.InActUrlForm):
        super().__init__(request=request)
        if inactform.is_valid():
            self.item_id = inactform.item_id
            self.url_id = inactform.url_id
            self.inact_url()
        else:
            self.errmsg = inactform.errmsg
            if inactform.item_id:
                self.item_id = inactform.item_id
            if inactform.url_id:
                self.url_id = inactform.url_id
    
    def inact_url(self):
        UrlQuery.update_url_active(item_id=self.item_id,
                                    url_id=self.url_id,
                                    isactive=UrlActive.INACTIVE)
        self.updateSuccess = True

class ActUrlPostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    url_id :int = const_value.NONE_ID
    updateSuccess :bool = False
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, actform :ppi.ActUrlForm):
        super().__init__(request=request)
        if actform.is_valid():
            self.item_id = actform.item_id
            self.url_id = actform.url_id
            self.act_url()
        else:
            self.errmsg = actform.errmsg
            if actform.item_id:
                self.item_id = actform.item_id
            if actform.url_id:
                self.url_id = actform.url_id
    
    def act_url(self):
        UrlQuery.update_url_active(item_id=self.item_id,
                                   url_id=self.url_id,
                                   isactive=UrlActive.ACTIVE)
        self.updateSuccess = True

class UpdateItemUrlPostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    updateSuccess :bool = False
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, upurlform :ppi.UpdateItemUrlForm):
        super().__init__(request=request)
        if upurlform.item_id:
            self.item_id = upurlform.item_id
        if not is_update_process_alive():
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

    def __init__(self, request, upurlform :ppi.UpdateItemAllUrlForm):
        super().__init__(request=request)
        if upurlform.return_user:
            self.return_user = True
        if upurlform.item_id:
            self.item_id = upurlform.item_id
        if not is_update_process_alive():
            self.errmsg = "更新できない状態です。サーバを確認して下さい。"
            return
        if upurlform.is_valid():
            self.update_data()
        else:
            self.errmsg = upurlform.errmsg
            
    
    def update_data(self):
        urlinitems = UrlQuery.get_act_urlinfo_by_item_id(self.item_id)
        for uii in urlinitems:
            sendTask(ScrOrder.UPDATE, uii.urlpath, str(const_value.NONE_ID))
        self.updateSuccess = True

class RemoveItemUrlPostContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    updateSuccess :bool = False
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, remurlform :ppi.RemoveItemUrlForm):
        super().__init__(request=request)
        if remurlform.is_valid():
            self.item_id = remurlform.item_id
            self.remove_data(remurlform.url_id)
        else:
            self.errmsg = remurlform.errmsg
            if remurlform.item_id:
                self.item_id = remurlform.item_id
    
    def remove_data(self, url_id:int):
        UrlQuery.delete_urlinitem(item_id=self.item_id, url_id=url_id)
        self.updateSuccess = True

class AddGroupPostContext(BaseTemplateValue):
    group_name :str = ""
    group_id :int = const_value.NONE_ID
    errmsg :str = ""
    addSuccess :bool = False
    POST_GROUP_NAME :str = filter_name.TemplatePostName.GROUP_NAME.value
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value

    def __init__(self, request, addgform :ppi.AddGroupForm):
        super().__init__(request=request)
        if addgform.is_valid():
            self.group_name = addgform.group_name
            self.add_group()
            return
        else:
            self.errmsg = addgform.errmsg
            if addgform.group_name:
                self.group_name = addgform.group_name
    
    def add_group(self):
        if not GroupQuery.get_group_by_name(name=self.group_name):
            group_id = GroupQuery.add_group(self.group_name)
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
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value
    ITEMACT_NAME: str =  filter_name.FilterQueryName.ACT.value    
    ITEMSORT_NAME: str = filter_name.FilterQueryName.ISORT.value
    POST_GROUP_ID : str = filter_name.TemplatePostName.GROUP_ID.value
    POST_GROUP_ITEM_LIST : str = filter_name.TemplatePostName.GROUP_ITEM_LIST.value

    def __init__(self, request, nfqg :ppi.NewestFilterQueryForGroup): #fd:Dict):
        fd = nfqg.get_filter_dict()
        super().__init__(
                request=request
                ,actstslist = ppi.get_actstslist(fd)
                ,itemSortList = ppi.get_item_sort_list(fd)
                ,groups = ppi.get_groups(fd)
                ,fquery=fd
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
            newest_list = NewestQuery.get_newest_data_for_edit_group(fd)
            self.res = self.get_newest_list_add_seleted(newest_list=newest_list, group_id=self.gfid)

    def get_newest_list_add_seleted(self, newest_list, group_id :int):
        gi_list = GroupQuery.get_group_item_by_group_id(group_id)
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
    def __init__(self, giform :ppi.GroupItemUpdateForm):
        if giform.is_valid():
            self.group_id = giform.group_id
            self.update_group_item(giform.group_item_list)
    
    def update_group_item(self, group_item_list):
        GroupQuery.update_group_item(self.group_id, group_item_list)


    def get_query(self):
        if self.group_id and self.group_id != const_value.NONE_ID:
            return f"?{filter_name.FilterQueryName.GID.value}={self.group_id}"
        return ""

class DeleteGroupInitContext(BaseTemplateValue):
    gid :int = const_value.NONE_ID
    groupname :str = ""
    POST_GROUP_ID :str = filter_name.TemplatePostName.GROUP_ID.value
    GROUPID_NAME :str = filter_name.FilterQueryName.GID.value

    def __init__(self, request, delgform :ppi.DeleteGroupForm):
        super().__init__(request=request)
        if delgform.is_valid():
            self.gid = delgform.group_id
            g = GroupQuery.get_group_by_group_id(self.gid)
            self.groupname = g.groupname

class DeleteGroupContext(DeleteGroupInitContext):
    errmsg :str = ""
    delSuccess :bool = False

    def __init__(self, request, delgform :ppi.DeleteGroupForm):
        super().__init__(request=request, delgform=delgform)
        if delgform.is_valid():
            self.delete_group()
            
    def delete_group(self):
        GroupQuery.del_group(self.gid)
        self.delSuccess = True

class RenameGroupNameInitContext(BaseTemplateValue):
    gid :int = const_value.NONE_ID
    before_groupname :str = ""
    POST_GROUP_ID :str = filter_name.TemplatePostName.GROUP_ID.value
    POST_GROUP_NAME :str = filter_name.TemplatePostName.GROUP_NAME.value
    GROUPID_NAME :str = filter_name.FilterQueryName.GID.value

    def __init__(self, request, rgnform :ppi.RenameGroupNameInitForm):
        super().__init__(request=request)
        if rgnform.is_valid():
            self.gid = rgnform.group_id
            g = GroupQuery.get_group_by_group_id(self.gid)
            self.before_groupname = g.groupname

class RenameGroupNameContext(BaseTemplateValue):
    gid :int = const_value.NONE_ID
    groupname :str = ""
    updateSuccess :bool = False
    POST_GROUP_ID :str = filter_name.TemplatePostName.GROUP_ID.value
    POST_GROUP_NAME :str = filter_name.TemplatePostName.GROUP_NAME.value
    GROUPID_NAME :str = filter_name.FilterQueryName.GID.value

    def __init__(self, request, rgnform :ppi.RenameGroupNameForm):
        super().__init__(request=request)
        if rgnform.is_valid():
            self.gid = rgnform.group_id
            self.groupname = rgnform.groupname
            self.rename_group()
    
    def rename_group(self):
        GroupQuery.update_group_name(group_id=self.gid, name=self.groupname)
        self.updateSuccess = True

class DeleteItemInitContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    itemname :str = ""
    POST_ITEM_ID :str = filter_name.TemplatePostName.ITEM_ID.value
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, request, diform :ppi.DeleteItemForm):
        super().__init__(request=request)
        if diform.is_valid():
            self.item_id = diform.item_id
            self.itemname = ItemQuery.get_item(self.item_id).name
        else:
            self.errmsg = diform.errmsg

class DeleteItemContext(BaseTemplateValue):
    item_id :int = const_value.NONE_ID
    itemname :str = ""
    POST_ITEM_ID :str = filter_name.TemplatePostName.ITEM_ID.value
    errmsg :str = ""
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value
    delSuccess :bool = False

    def __init__(self, request, diform :ppi.DeleteItemForm):
        super().__init__(request=request)
        if not diform.is_valid():
            self.errmsg = diform.errmsg
            return
        self.item_id = diform.item_id
        self.itemname = ItemQuery.get_item(self.item_id).name
        self.delete_data()

    def delete_data(self):
        ItemQuery.delete_item_relation_by_item_id(self.item_id)
        self.delSuccess = True
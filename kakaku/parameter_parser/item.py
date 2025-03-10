from urllib.parse import urlencode, parse_qs
from datetime import datetime

from fastapi import Form, Cookie
from pydantic import BaseModel

from common.filter_name import (
    ActFilterName,
    FilterQueryName,
    ItemDetailQueryName,
    ItemSortName,
    FilterOnOff,
    StoreListSortName,
    StoreTermsConfiguredFilterName,
    ItemPurchaseSortName,
    UrlSortName,
    ExtractStoreSortName,
    TemplatePostName,
    ItemDetailTimePeriodName,
    OnlineStoreCopyTypeName,
)
from common.templates_string import HTMLOption

from common import const_value, read_config
from common.util import is_num
from accessor.item import GroupQuery
from sqlalchemy.orm import Session

from parameter_parser.util import is_suppoer_url, is_valid_id
from parameter_parser.storepostage import ItemCombStore, FormDataConvert
from itemcomb.prefecture import PrefectureName


class NewestFilterQuery:
    gid: str = ""
    act: str = ""
    store: str = ""
    isort: str = ""
    zaiko: str = ""
    prmin: str = ""
    prmax: str = ""
    cfilter_str: str = ""

    is_c_able: bool = False

    def __init__(
        self,
        gid: str = "",
        act: str = "",
        store: str = "",
        isort: str = "",
        zaiko: str = "",
        prmin: str = "",
        prmax: str = "",
        cfilter_str: str | None = Cookie(None),
    ):
        if (
            not gid
            and not act
            and not store
            and not isort
            and not zaiko
            and not prmin
            and not prmax
        ) and cfilter_str:
            self.set_cookie_query(cfilter_str)
        else:
            self.set_query(
                gid=gid,
                act=act,
                store=store,
                isort=isort,
                zaiko=zaiko,
                prmin=prmin,
                prmax=prmax,
            )

    def set_query(
        self,
        gid: str = "",
        act: str = "",
        store: str = "",
        isort: str = "",
        zaiko: str = "",
        prmin: str = "",
        prmax: str = "",
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
        if prmin and is_num(prmin) and int(prmin) >= const_value.INIT_PRICE:
            self.prmin = prmin
        if prmax and is_num(prmax) and int(prmax) >= const_value.INIT_PRICE:
            while True:
                if self.prmin and int(self.prmin) > int(prmax):
                    break
                self.prmax = prmax
                break

    def set_cookie_query(self, cfilter_str: str):
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
        if self.cfilter_str is not None:
            if self.cfilter_str != urlencode(self.get_qfilter_dict()):
                return True
        return False

    def get_filter_dict(self) -> dict:
        if self.cfilter_str:
            return self.queryToDict(self.cfilter_str)
        return self.get_qfilter_dict()

    def get_cookie(self) -> str:
        return urlencode(self.get_filter_dict())

    @staticmethod
    def queryToDict(filter: str) -> dict:
        pqs = parse_qs(filter)
        results = {}
        for k, v in pqs.items():
            if type(v) is list:
                results[k] = v[0]
            else:
                results[k] = v
        return results

    def get_qfilter_dict(self) -> dict:
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
        if self.prmin:
            results[FilterQueryName.PRMIN.value] = self.prmin
        if self.prmax:
            results[FilterQueryName.PRMAX.value] = self.prmax
        return results


class ItemDetailQuery:
    itemid: str = ""
    periodid: str = ""
    store: str = ""
    press: str = ""

    def __init__(
        self, itemid: str = "", periodid: str = "", store: str = "", press: str = ""
    ):
        if is_valid_id(itemid):
            self.itemid = itemid
        if is_valid_id(periodid) and self.is_valid_period_id(periodid):
            self.periodid = periodid
        if store and store.isdigit():
            self.store = store
        if press and press.isdigit():
            self.press = press

    def is_valid_period_id(self, pid: str):
        return ItemDetailTimePeriodName.hasId(int(pid))

    def get_filter_dict(self) -> dict:
        results = {}
        if self.itemid:
            results[ItemDetailQueryName.ITEMID.value] = self.itemid
        if self.periodid:
            results[ItemDetailQueryName.PERIODID.value] = self.periodid
        if self.store:
            results[FilterQueryName.STORE.value] = self.store
        if self.press:
            results[FilterQueryName.PRESS.value] = self.press
        return results


class ItemDetailChartQuery:
    itemid: str = ""
    min_date: str = ""
    max_date: str = ""
    period: str = ""
    start: str = ""
    each: str = ""

    def __init__(
        self,
        itemid: str = "",
        min_date: str = "",
        max_date: str = "",
        period: str = "",
        start: str = "",
        each: str = "",
    ):
        if is_valid_id(itemid):
            self.itemid = itemid
        if min_date and self.is_valid_date(min_date):
            self.min_date = min_date
        if max_date and self.is_valid_date(max_date):
            self.max_date = max_date
        if is_valid_id(period):
            self.period = period
        if start:
            self.start = start
        if each:
            self.each = each

    def is_valid_date(self, value: str):
        fmt = "%Y-%m-%d"
        try:
            datetime.strptime(value, fmt)
        except Exception:
            return False
        return True

    def get_filter_dict(self) -> dict:
        results = {}
        if self.itemid:
            results[ItemDetailQueryName.ITEMID.value] = self.itemid
        if self.min_date:
            results[FilterQueryName.MIN_DATE.value] = self.min_date
        if self.max_date:
            results[FilterQueryName.MAX_DATE.value] = self.max_date
        if self.period:
            results[FilterQueryName.PERIOD.value] = self.period
        if self.start:
            results[FilterQueryName.START.value] = self.start
        if self.each:
            results[FilterQueryName.EACH.value] = self.each
        return results


def get_compress_filter_checked(f: dict) -> str:
    if (
        FilterQueryName.PRESS.value in f
        and int(f[FilterQueryName.PRESS.value]) == FilterOnOff.ON
    ):
        return HTMLOption.CHECKED.value
    return ""


class TemplatesItemSort(BaseModel):
    name: str
    id: int
    text: str
    selected: str = ""


def get_item_sort_list(f: dict) -> list:
    results = [
        TemplatesItemSort(name=i.qname, id=i.id, text=i.jname) for i in ItemSortName
    ]
    if FilterQueryName.ISORT.value not in f:
        return results
    for r in results:
        if int(r.id) == int(f[FilterQueryName.ISORT.value]):
            r.selected = HTMLOption.SELECTED.value
    return results


def convert_itemsort_to_extractstoresort(f: dict):
    pass


def get_extract_store_sort_list(f: dict) -> list[TemplatesItemSort]:
    results = [
        TemplatesItemSort(name=i.qname, id=i.id, text=i.jname)
        for i in ExtractStoreSortName
    ]
    if FilterQueryName.ESSORT.value not in f:
        return results
    for r in results:
        if int(r.id) == int(f[FilterQueryName.ESSORT.value]):
            r.selected = HTMLOption.SELECTED.value
    return results


class TemplatesActStatus(BaseModel):
    id: int
    text: str
    selected: str = ""


def get_actstslist(f: dict) -> list:
    results = [TemplatesActStatus(id=a.id, text=a.text) for a in ActFilterName]
    if FilterQueryName.ACT.value not in f:
        return results
    for r in results:
        if r.id == int(f[FilterQueryName.ACT.value]):
            r.selected = HTMLOption.SELECTED.value
            break
    return results


class TemplatesGroup(BaseModel):
    group_id: int
    groupname: str = ""
    selected: str = ""


def get_groups(db: Session, f: dict) -> list:
    results = [
        TemplatesGroup(group_id=g.group_id, groupname=g.groupname)
        for g in GroupQuery.get_all(db)
    ]
    if FilterQueryName.GID.value not in f:
        return results
    for r in results:
        if r.group_id == int(f[FilterQueryName.GID.value]):
            r.selected = HTMLOption.SELECTED.value
            break
    return results


class AddItemUrlForm:
    item_name: str = ""
    url_path: str = ""
    search_query: str = ""
    errmsg: str = ""

    def __init__(
        self,
        item_name: str | None = Form(None),
        url_path: str | None = Form(None),
        search_query: str | None = Form(None),
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


class AddUrlForm:
    item_id: int = const_value.NONE_ID
    url_path: str = ""
    search_query: str = ""
    errmsg: str = ""

    def __init__(
        self,
        item_id: str | None = Form(None),
        url_path: str | None = Form(None),
        search_query: str | None = Form(None),
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


class UpdateItemNameForm:
    item_id: int = const_value.NONE_ID
    item_name: str = ""
    errmsg: str = ""

    def __init__(
        self, item_id: str | None = Form(None), item_name: str | None = Form(None)
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
        if not self.item_name or len(self.item_name) == 0:
            self.errmsg = "アイテム名は1文字以上入れて下さい"
            return False
        return True


class ItemIdForm:
    item_id: int = const_value.NONE_ID
    errmsg: str = ""

    def __init__(
        self,
        item_id: str | None = Form(None),
    ):
        if is_valid_id(item_id):
            self.item_id = int(item_id)

    def is_valid(self):
        if self.item_id == const_value.NONE_ID:
            self.errmsg = "アイテムが不明です"
            return False
        return True


class ItemIdUrlIdForm:
    item_id: int = const_value.NONE_ID
    url_id: int = const_value.NONE_ID
    errmsg: str = ""

    def __init__(
        self, item_id: str | None = Form(None), url_id: str | None = Form(None)
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
    item_id: int = const_value.NONE_ID
    url_path: str = ""
    errmsg: str = ""

    def __init__(
        self,
        item_id: str | None = Form(None),
        url_path: str | None = Form(None),
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


class UpdateItemAllUrlForm:
    item_id: int = const_value.NONE_ID
    return_user: int = 0
    errmsg: str = ""

    def __init__(
        self,
        item_id: str | None = Form(None),
        return_user: str | None = Form(None),
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
    group_name: str = ""
    errmsg: str = ""

    def __init__(
        self,
        group_name: str | None = Form(None),
    ):
        if group_name:
            self.group_name = group_name

    def is_valid(self):
        if self.group_name and len(self.group_name) > 0:
            return True
        return False


class NewestFilterQueryForGroup(NewestFilterQuery):
    pass


class GroupItemUpdateForm:
    group_item_list: list[int] = []
    group_id: int = const_value.NONE_ID

    def __init__(
        self,
        group_id: str | None = Form(None),
    ):
        if is_valid_id(group_id):
            self.group_id = int(group_id)

    def set_group_item_list(self, form_dict: dict[str, list]):
        if TemplatePostName.GROUP_ITEM_LIST.value not in form_dict:
            return
        results: list[int] = []
        for item_id in form_dict[TemplatePostName.GROUP_ITEM_LIST.value]:
            if is_valid_id(item_id):
                results.append(int(item_id))
        self.group_item_list = results

    def is_valid(self):
        if self.group_id == const_value.NONE_ID:
            return False
        return True


class GroupIdForm:
    group_id: int = const_value.NONE_ID

    def __init__(
        self,
        group_id: str | None = Form(None),
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
    group_id: int = const_value.NONE_ID
    groupname: str = ""

    def __init__(
        self,
        group_id: str | None = Form(None),
        group_name: str | None = Form(None),
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


class AnalysisBaseQuery:
    itemid: str = ""
    atid: str = ""

    def __init__(
        self,
        itemid: str = "",
        atid: str = "",
    ):
        if is_valid_id(itemid):
            self.itemid = itemid
        if is_valid_id(atid):
            self.atid = atid


class ItemPurchaseFilterQuery:
    act: str = ""
    psort: str = ""
    gid: str = ""

    def __init__(
        self,
        act: str = "",
        psort: str = "",
        gid: str = "",
    ):
        if act and act.isdigit() and ActFilterName.hasValue(int(act)):
            self.act = act
        else:
            self.act = str(ActFilterName.ACT.id)
        if psort and psort.isdigit() and ItemPurchaseSortName.hasId(int(psort)):
            self.psort = psort
        if is_valid_id(gid):
            self.gid = gid

    def get_filter_dict(self) -> dict:
        results = {}
        if self.act:
            results[FilterQueryName.ACT.value] = self.act
        if self.psort:
            results[FilterQueryName.PSORT.value] = self.psort
        if self.gid:
            results[FilterQueryName.GID.value] = self.gid
        return results


def get_item_purchase_sort_list(f: dict) -> list:
    results = [
        TemplatesItemSort(name=i.qname, id=i.id, text=i.jname)
        for i in ItemPurchaseSortName
    ]
    if FilterQueryName.PSORT.value not in f:
        return results
    for r in results:
        if int(r.id) == int(f[FilterQueryName.PSORT.value]):
            r.selected = HTMLOption.SELECTED.value
    return results


class UrlListFilterQuery:
    act: str = ""
    usort: str = ""

    def __init__(
        self,
        act: str = "",
        usort: str = "",
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


def get_url_sort_list(f: dict) -> list:
    results = [
        TemplatesItemSort(name=i.qname, id=i.id, text=i.jname) for i in UrlSortName
    ]
    if FilterQueryName.USORT.value not in f:
        return results
    for r in results:
        if int(r.id) == int(f[FilterQueryName.USORT.value]):
            r.selected = HTMLOption.SELECTED.value
    return results


class ExtractStoreFilterQuery:
    gid: str = ""
    act: str = ""
    ex_store: str = ""
    essort: str = ""
    zaiko: str = ""
    prmin: str = ""
    prmax: str = ""

    def __init__(
        self,
        gid: str = "",
        act: str = "",
        ex_store: str = "",
        store: str = "",
        essort: str = "",
        isort: str = "",
        zaiko: str = "",
        prmin: str = "",
        prmax: str = "",
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
        elif isort and isort.isdigit() and ItemSortName.hasId(int(isort)):
            convert_result = self.convert_itemsort_to_essort(int(isort))
            if convert_result:
                self.essort = str(convert_result)
        if zaiko and zaiko.isdigit() and int(zaiko) == FilterOnOff.ON:
            self.zaiko = zaiko
        if prmin and is_num(prmin) and int(prmin) >= const_value.INIT_PRICE:
            self.prmin = prmin
        if prmax and is_num(prmax) and int(prmax) >= const_value.INIT_PRICE:
            while True:
                if self.prmin and int(self.prmin) > int(prmax):
                    break
                self.prmax = prmax
                break

    def get_filter_dict(self) -> dict:
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
        if self.prmin:
            results[FilterQueryName.PRMIN.value] = self.prmin
        if self.prmax:
            results[FilterQueryName.PRMAX.value] = self.prmax
        return results

    @classmethod
    def convert_itemsort_to_essort(cls, isort: int) -> int | None:
        if isort == ItemSortName.STORE_NAME.id:
            return None
        if ExtractStoreSortName.hasId(isort):
            return isort
        return None


def get_in_stock_filter_checked(f: dict) -> str:
    if (
        FilterQueryName.ZAIKO.value in f
        and int(f[FilterQueryName.ZAIKO.value]) == FilterOnOff.ON
    ):
        return HTMLOption.CHECKED.value
    return ""


class StoreListFilterQuery:
    sort: str = str(StoreListSortName.OLD_STORE.id)
    confed: str = ""

    def __init__(
        self,
        sort: str = "",
        confed: str = "",
    ):
        if sort and sort.isdigit() and StoreListSortName.hasId(int(sort)):
            self.sort = sort
        if (
            confed
            and confed.isdigit()
            and StoreTermsConfiguredFilterName.hasId(int(confed))
        ):
            self.confed = confed

    def get_filter_dict(self) -> dict:
        results = {}
        if self.sort:
            results[FilterQueryName.SORT.value] = self.sort
        if self.confed:
            results[FilterQueryName.CONFED.value] = self.confed
        return results


def get_store_sort_list(f: dict) -> list:
    results = [
        TemplatesItemSort(name=i.qname, id=i.id, text=i.jname)
        for i in StoreListSortName
    ]
    if FilterQueryName.SORT.value not in f:
        return results
    for r in results:
        if int(r.id) == int(f[FilterQueryName.SORT.value]):
            r.selected = HTMLOption.SELECTED.value
    return results


def get_store_terms_configured_list(f: dict) -> list:
    results = [
        TemplatesItemSort(name=i.qname, id=i.id, text=i.jname)
        for i in StoreTermsConfiguredFilterName
    ]
    if FilterQueryName.CONFED.value not in f:
        return results
    for r in results:
        if int(r.id) == int(f[FilterQueryName.CONFED.value]):
            r.selected = HTMLOption.SELECTED.value
    return results


class EditShippingConditionForm:
    errmsg: str = ""
    store_list: list[ItemCombStore] = []

    def __init__(
        self,
    ):
        pass

    def set_store_list(self, stores: list[str]):
        if stores:
            self.store_list = FormDataConvert.parse_stores(stores=stores)


class DeleteStoreForm:
    store_id: int = const_value.NONE_ID
    errmsg: str = ""

    def __init__(
        self,
        store_id: str | None = Form(None),
    ):
        if is_valid_id(store_id):
            self.store_id = store_id

    def is_valid(self):
        if self.store_id == const_value.NONE_ID:
            self.errmsg = "店舗が不明です"
            return False
        return True


def is_valid_pref(pref: str):
    if not pref:
        return False
    if pref == PrefectureName.get_country_wide_name():
        return True
    if pref in PrefectureName.get_all_prefecturename():
        return True
    return False


class OnlineStoreListFilterQuery:
    sort: str = str(StoreListSortName.OLD_STORE.id)
    confed: str = ""
    pref: str = ""
    store: str = ""

    def __init__(
        self,
        sort: str = "",
        confed: str = "",
        pref: str = "",
        store: str = "",
    ):
        if sort and sort.isdigit() and StoreListSortName.hasId(int(sort)):
            self.sort = sort
        if (
            confed
            and confed.isdigit()
            and StoreTermsConfiguredFilterName.hasId(int(confed))
        ):
            self.confed = confed
        if is_valid_pref(pref):
            self.pref = pref
        elif "all" != pref:
            self.pref = str(read_config.get_default_shipping_prefecture_name())
        if store and store.isdigit():
            self.store = store

    def get_filter_dict(self) -> dict:
        results = {}
        if self.sort:
            results[FilterQueryName.SORT.value] = self.sort
        if self.confed:
            results[FilterQueryName.CONFED.value] = self.confed
        if self.pref:
            results[FilterQueryName.PREF.value] = self.pref
        if self.store:
            results[FilterQueryName.STORE.value] = self.store
        return results


class OnlineStoreCopyToMyQuery:
    online_store_copy_type: int
    pref: str = ""

    def __init__(
        self,
        osctype: int,
        pref: str,
    ):
        if osctype and OnlineStoreCopyTypeName.hasId(osctype):
            self.online_store_copy_type = osctype
        if is_valid_pref(pref):
            self.pref = pref

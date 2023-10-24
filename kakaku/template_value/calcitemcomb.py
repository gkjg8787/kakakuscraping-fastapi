from typing import List, Dict, Union
import re
from enum import Enum
import json

from pydantic import BaseModel

from sqlalchemy.orm import Session

from common import (
    filter_name,
    const_value,
    templates_string,
    read_config,
)
from template_value import BaseTemplateValue
import parameter_parser.item as ppi
import parameter_parser.store as pps
import parameter_parser.calcitemcomb as ppc 
from accessor.item import (
    NewestQuery,
)
from itemcomb.storepostage import (
    getAndRegistShippingTermsByItemId,
    StorePostageResultName,
    update_shippingterms,
)
from itemcomb.sumitemcomb_adapt import startCalcSumitemComb
import model.store as mstore

from itemcomb.surugaya_postage_util import getPrefList, funcstart
from itemcomb.surugaya_postage.const_value import DEFAULT_PREF

class ItemSelectionContext(BaseTemplateValue):
    res :List
    res_length :int = 0
    actstslist :List
    itemSortList :List
    groups :List
    storelist :List
    fquery :Dict
    ZAIKO_CHECKED : str = ""
    GROUPID_NAME :str = filter_name.FilterQueryName.GID.value
    ITEMACT_NAME :str =  filter_name.FilterQueryName.ACT.value
    ITEMSORT_NAME :str = filter_name.FilterQueryName.ISORT.value
    EQST_NAME :str = filter_name.FilterQueryName.STORE.value
    ITEMID_Q_NAME :str = filter_name.ItemDetailQueryName.ITEMID.value
    ITEM_LIMIT :int = 0
    STOCK_NAME :str = filter_name.FilterQueryName.ZAIKO.value
    STOCK_VALUE :int = filter_name.FilterOnOff.ON

    def __init__(self, request, nfq :ppi.NewestFilterQuery, db :Session):
        fd = nfq.get_filter_dict()
        super().__init__(request=request
                         ,res=NewestQuery.get_newest_data(db, filter=fd)
                        ,actstslist = ppi.get_actstslist(fd)
                        ,itemSortList = ppi.get_item_sort_list(fd)
                        ,groups = ppi.get_groups(db, f=fd)
                        ,storelist = []
                        ,fquery=fd
                        ,ZAIKO_CHECKED=ppi.get_in_stock_filter_checked(fd)
                         )
        item_limit = read_config.get_itemcomb_select_limit()
        if item_limit and str(item_limit).isdigit() and int(item_limit) > 0:
            self.ITEM_LIMIT = int(item_limit)
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

class OperatorName(Enum):
    GT = ("gt", "<")
    GE = ("ge", "<=")
    LT = ("lt", ">")
    LE = ("le", ">=")

    def __init__(self, lower :str, symbol :str):
        self.lower = lower
        self.symbol = symbol


class SelecteTermsOperator():
    gt :str = ""
    ge :str = ""
    lt :str = ""
    le :str = ""

class Terms():
    terms_num :int
    terms_index :int
    boundary1 :str = ""
    boundary2 :str = ""
    ope :List[SelecteTermsOperator]
    postage :str = ""
    created_at :str = ""


    def __init__(self, terms_index, boundary, postage, created_at):
        self.terms_index = self.__get_int_or_default(terms_index)
        self.terms_num = self.terms_index
        if boundary:
            self.ope = []
            self.set_boundary(boundary)
        else:
            self.ope = [self.create_SelecteTermsOperator('')]
        if postage:
            self.postage = postage
        if created_at:
            self.created_at = created_at
    
    @classmethod
    def __get_int_or_default(cls, val) -> int:
        if not val or not str(val).isdecimal():
            return const_value.INIT_TERMS_ID
        return int(val)


    def create_SelecteTermsOperator(self, opestr) -> SelecteTermsOperator:
        res = SelecteTermsOperator()
        selected = templates_string.HTMLOption.SELECTED.value
        if opestr == OperatorName.GE.symbol:
            res.ge = selected
            return res
        if opestr == OperatorName.GT.symbol:
            res.gt = selected
            return res
        if opestr == OperatorName.LE.symbol:
            res.le = selected
            return res
        if opestr == OperatorName.LT.symbol:
            res.lt = selected
            return res
        return res

    def set_boundary(self, boundary):
        pattern = r'([0-9]*)([<|>]=?)'
        boudarydivptn = re.compile(pattern)
        bv = boudarydivptn.findall(boundary)
        if len(bv) == 0:
            self.boundary1 = ''
            self.ope.append(self.create_SelecteTermsOperator(''))
        if len(bv) == 1 or len(bv) == 2:
            self.boundary1 = bv[0][0]
            self.ope.append(self.create_SelecteTermsOperator(bv[0][1]))
        if len(bv) == 2:
            self.boundary2 = bv[1][0]
            self.ope.append(self.create_SelecteTermsOperator(bv[1][1]))
        return


class StoreShippingTerms():
    store_id :Union[int,str]
    storename :str
    terms_list :List[Terms]

    def __init__(self, store_id, storename):
        self.store_id = self.__get_int_or_blank(store_id)
        self.storename = storename
        self.terms_list = []

    def add_terms(self, terms :Terms):
        self.terms_list.append(terms)    


    @staticmethod
    def __get_int_or_blank(val):
        if not val or not str(val).isdecimal():
            return ''
        return int(val)



class ShippingConditionContext(BaseTemplateValue):
    item_id_list :List[int] = []
    store_list :List = []
    errmsg :str = ""
    POST_ITEM_ID :str = filter_name.TemplatePostName.ITEM_ID.value
    POST_STORENAME :str = filter_name.TemplatePostName.STORE_NAME.value

    def __init__(self, request, scq :ppc.ShippingConditionQuery, db :Session):
        super().__init__(request=request)
        if not scq.is_valid():
            self.errmsg = scq.errmsg
            return
        self.item_id_list = scq.item_id_list
        results = getAndRegistShippingTermsByItemId(db, itemids=self.item_id_list)
        if StorePostageResultName.ERROR in results:
            self.errmsg = results[StorePostageResultName.ERROR].value
            return
        if StorePostageResultName.RESULT in results:
            self.store_list = self.convert_to_store_list(results[StorePostageResultName.RESULT])
    
    def convert_to_store_list(self, res_list :List[Dict]) -> List[StoreShippingTerms]:
        results :Dict[str, StoreShippingTerms]= {}
        for res in res_list:
            t = Terms(terms_index=res['terms_id'],
                                boundary=res['boundary'],
                                postage=res['postage'],
                                created_at=res['created_at'],)
            if res['storename'] in results:
                results[res['storename']].add_terms(t)
                continue
            else:
                sst = StoreShippingTerms(store_id=res['store_id'],
                                        storename=res['storename'],)
                results[res['storename']] = sst
                sst.add_terms(t)
                continue
        return [a for a in results.values()]


class ResultItem(BaseModel):
    item_number : int
    item_name :str = ""
    store_name :str = ""
    item_price : int

class ResultStoreItem(BaseModel):
    name :str
    price :int

class ResultStore(BaseModel):
    name :str
    sum_pos_out :int
    postage :int
    sum_pos_in :int
    items :List[ResultStoreItem] = []

class ItemCombCalcResultContext(BaseTemplateValue):
    item_count :int = 0
    itemnames :str = ""
    sum_pos_in :str = ""
    sum_postage :str = ""
    item_list :List[ResultItem] = []
    store_list :List = []

    def __init__(self, request, icrf :ppc.ItemCombinationResultForm, db :Session):
        super().__init__(request=request)
        if not icrf.is_valid() or len(icrf.store_list) == 0:
            return
        self.update_shippingterms_data(db, icrf=icrf)
        #print(f"icrf.store_list={icrf.store_list}")
        res = startCalcSumitemComb(db, itemidlist=icrf.item_id_list)
        #print(f"res={res}")
        self.set_convert_result(json.loads(res))
    
    def set_convert_result(self, res):
        storeres = {}
        for k,v in res.items():
            if k == 'sum_pos_in':
                self.sum_pos_in = v
                continue
            if k == 'sum_postage':
                self.sum_postage = v
                continue
            storeres[k] = v
        self.item_list = self._create_item_list(storeres)
        self.store_list = self._create_store_list(storeres)
        self._set_item_names_count(storeres)
    
    def _create_store_list(self, storeres):
        results :List[ResultStore] = []
        for storename, val in storeres.items():
            rs = ResultStore(name=str(storename),
                             sum_pos_out=int(val['sum_pos_out']),
                             postage=int(val['postage']),
                             sum_pos_in=int(val['sum_pos_out'])+int(val['postage']),
                             items=list(),
                             )
            for item in storeres[storename]['items']:
                rsi = ResultStoreItem(name=item['itemname'],
                                      price=item['price'],
                                      )
                rs.items.append(rsi)
            results.append(rs)
        return results

    def _create_item_list(self, storeres):
        item_num = 0
        results :List[ResultItem] = []
        for storename in storeres:
            for item in storeres[storename]['items']:
                results.append(ResultItem(item_number=item_num,
                                          item_name=item['itemname'],
                                          store_name=storename,
                                          item_price=item['price'],
                                          )
                               )
                item_num += 1
        return results

    
    def _set_item_names_count(self, storeres):
        items = []
        for k, v in storeres.items():
            for val in v['items']:
                items.append(val['itemname'])
                self.item_count += 1
        self.itemnames = '、'.join(items)

    @staticmethod
    def update_shippingterms_data(db :Session, icrf : ppc.ItemCombinationResultForm):
        store_id_list :List[int] = []
        storepostage_list :List[mstore.StorePostage] = []
        for store in icrf.store_list:
            store_id_list.append(store.store_id)
            sps = store.toStorePostages()
            if len(sps) > 0:
                storepostage_list.extend(sps)
        
        update_shippingterms(db=db,
                             store_id_list=store_id_list,
                             storepostage_list=storepostage_list)

class StoreShippingInfo:
    shop_name :str = ""
    url :str = ""
    shop_id :int
    postage :Union[int,None] = None
    national_fee :Union[int,None] = None
    local_fee :Union[int,None] = None

    def __init__(self, res :Dict):
        if 'shop_name' in res:
            self.shop_name = res['shop_name']
        if 'href' in res:
            self.url = res['href']
        if 'shop_id' in res:
            self.shop_id = int(res['shop_id'])
        if 'postage' in res:
            self.set_postages(res['postage'])

    
    def set_postages(self, postages):
        for p in postages:
            if 'national_fee' in p \
                and not self.national_fee\
                and p['national_fee']:
                self.national_fee = int(p['national_fee'])
            if 'fee' in p\
                and not self.local_fee\
                and p['fee']:
                self.local_fee = int(p['fee'])
                continue
        if not self.national_fee:
            self.postage = self.local_fee
        elif not self.local_fee:
            self.postage = self.national_fee
        elif self.national_fee != 0 and self.local_fee != 0:
            self.postage =  self.local_fee


    

class ShippingResult:
    shipping_list :List[StoreShippingInfo] = []

    def __init__(self, result :Dict):
        self.shipping_list = list()
        if 'result' in result:
            for r in result['result']:
                ssi = StoreShippingInfo(r)
                self.shipping_list.append(ssi)
    def get_list(self):
        return self.shipping_list

class DestinationPrefecture(BaseModel):
    name :str = ""
    selected :str = ""


class SearchShippingContext(BaseTemplateValue):
    PREF_NAME :str = filter_name.FilterQueryName.PREF.value
    SEARCH_WORD_NAME :str = filter_name.FilterQueryName.WORD.value
    sword :str = ""
    pref_list :List[str] = []
    search_result :List = []
    errmsg = ""

    def __init__(self, request, ssq :ppc.SearchShippingQuery):
        super().__init__(request=request)
        if not ssq.pref:
            pref = DEFAULT_PREF
        else:
            pref = ssq.pref
        #print(pref)
        raw_pref_list = getPrefList()
        self.pref_list = self.create_pref_list(raw_pref_list, pref)
        self.sword = ssq.word
        if not ssq.is_valid():
            self.errmsg = ssq.errmsg
            return
        res = funcstart(storename=ssq.word, exact=False, prefectures=[pref])
        self.search_result = self.create_search_result(res)
        if len(self.search_result) == 0:
            self.errmsg = "見つかりませんでした"
            return
    
    def create_pref_list(self, raw_pref_list, query_pref :str):
        results :List[DestinationPrefecture] = []
        for pref in raw_pref_list:
            dp = DestinationPrefecture(name=pref)
            if pref == query_pref:
                dp.selected = templates_string.HTMLOption.SELECTED.value
            results.append(dp)
        return results

    def create_search_result(self, res):
        #print(res)
        sr = ShippingResult(res)
        return sr.get_list()



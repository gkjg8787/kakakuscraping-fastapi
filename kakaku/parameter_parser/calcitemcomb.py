from typing import List, Dict, Optional, Union
import re

from fastapi import Query, Form, Request
from pydantic import BaseModel

from parameter_parser.util import is_valid_id

from common.filter_name import ItemCombPostKey
from common.templates_string import ItemCombSelectValue

import model.store as mstore

class ShippingConditionQuery():
    item_id_list : List[int] = []
    errmsg :str = ""

    def __init__(self,
                 itemid :List[str] = Query(),
                 ):
        if itemid:
            results :List[int] = []
            for id in itemid:
                if is_valid_id(id):
                    results.append(int(id))
            self.item_id_list = results
    
    def is_valid(self):
        if len(self.item_id_list) == 0:
            self.errmsg = "アイテムが指定されていません"
            return False
        return True

class ItemCombTerms(BaseModel):
    terms_id :int
    boundary1 :str = ""
    b_ope1 :str = ""
    boundary2 :str = ""
    b_ope2 :str = ""
    postage :str = ""

    @staticmethod
    def _is_valid_int(val :str):
        if len(val) > 0 and val.isdecimal() and int(val) >= 0:
            return True
        return False
    
    def is_valid_terms(self):
        if self._is_valid_int(self.postage):
            return True
        return False
    
    def create_boundary(self) -> str:
        result :str = ""
        boundary1 = ""
        if len(self.boundary1) > 0 \
            and self._is_valid_int(self.boundary1) \
            and self.b_ope1:
            boundary1 = f"{self.boundary1}{self._convertToSymbol(self.b_ope1)}"
        else:
            boundary1 = "0<="
        boundary2 = ""
        if len(self.boundary2) > 0 \
            and self._is_valid_int(self.boundary2) \
            and self.b_ope2:
            boundary2 = f"{self.boundary2}{self._convertToSymbol(self.b_ope2)}"
        result = boundary1
        if boundary2:
            result = f"{result}:{boundary2}"
        return result
    
    def _convertToSymbol(self, ope :str) -> str:
        if ope == "gt":
            return "<"
        if ope == "ge":
            return "<="
        if ope == "lt":
            return ">"
        if ope == "le":
            return ">="

class ItemCombStore(BaseModel):
    store_id :int
    storename :str
    terms_list :List[ItemCombTerms]

    def toStorePostages(self) -> List[mstore.StorePostage]:
        results :List[mstore.StorePostage] = []
        for t in self.terms_list:
            if not t.is_valid_terms():
                continue
            sp = mstore.StorePostage(store_id=self.store_id,
                                     terms_id=t.terms_id,
                                     boundary=t.create_boundary(),
                                     postage=t.postage)
            results.append(sp)
        return results

class ItemCombinationResultForm(BaseModel):
    item_id_list :List[int] = []
    store_list :List[ItemCombStore] = []
    errmsg :str = ""

    def __init__(self,
                 item_id :List[str] = Form(),
                 ):
        super().__init__()
        if item_id:
            results :List[int] = []
            for id in item_id:
                if is_valid_id(id):
                    results.append(int(id))
            self.item_id_list = results


    
    def is_valid(self):
        if len(self.item_id_list) == 0:
            self.errmsg = "アイテムが指定されていません"
            return False
        return True
    
    def set_store_list(self, stores):
        if stores:
            self.store_list = self.parse_stores(stores)

    @classmethod
    def parse_stores(cls, stores):
        results :Dict[int, ItemCombStore]= {}
        brakets_ptn = "\[(.*?)\]"
        bcomp = re.compile(brakets_ptn)
        for store in stores:
            m = bcomp.findall(store)
            v = store.split("]=")
            #print(f"m_len={len(m)}, m={m}, v={v}")
            store_id = cls._get_store_id(m)
            if not store_id:
                raise KeyError('PostKey Error : store_id')
            if len(m) == 2 and len(v) > 1:
                if m[1] == ItemCombPostKey.STORENAME:
                    ics = ItemCombStore(store_id=store_id,
                                  storename=v[1],
                                  terms_list=list(),
                                  )
                    results[store_id] = ics
                    continue
            if len(m) > 2 and len(v) > 1:
                if m[1] != ItemCombPostKey.TERMS:
                    raise KeyError('PostKey Error : terms')
                terms_id = cls._get_terms_id(m)
                if not terms_id:
                    raise KeyError('PostKey Error : terms_id')
                if not store_id in results:
                    raise RuntimeError(f'Not Found Results Object = {results}')
                ics = results[store_id]
                #print(f"ics={ics}")
                ict = cls._get_itemcombterms(ics=ics, terms_id=terms_id)
                if m[3] == ItemCombPostKey.BOUNDARY:
                    cls._set_boundary(ict, v[1])
                elif m[3] == ItemCombPostKey.OPE:
                    cls._set_operator(ict, v[1])
                elif m[3] == ItemCombPostKey.POSTAGE:
                    ict.postage = v[1]
                    
        return [v for v in results.values()]

    @staticmethod
    def _get_store_id(postary):
        if is_valid_id(postary[0]):
            return int(postary[0])
        return None
    
    @staticmethod
    def _get_terms_id(postary):
        if is_valid_id(postary[2]):
            return int(postary[2])
        return None
    
    @staticmethod
    def _get_itemcombterms(ics:ItemCombStore, terms_id:int) -> ItemCombTerms:
        ict :Optional[ItemCombTerms] = None
        if len(ics.terms_list) == 0:
            ict = ItemCombTerms(terms_id=terms_id)
            ics.terms_list = [ict]
        else:
            for t in ics.terms_list:
                if t.terms_id == terms_id:
                    return t
            if ict is None:
                ict = ItemCombTerms(terms_id=terms_id)
                ics.terms_list.append(ict)
        return ict
    
    @staticmethod
    def _set_boundary(ict:ItemCombTerms, value):
        #print(f"set boundary boundary={value}, ict={ict}")
        if len(ict.boundary1) != 0:
            ict.boundary2 = value
            return
        if len(ict.boundary1) == 0:
            ict.boundary1 = value
            return
        if ict.boundary2:
            raise RuntimeError('Many PostKey : Boundary')
    
    @staticmethod
    def _set_operator(ict:ItemCombTerms, value):
        if value == ItemCombSelectValue.NO_SELECTED.value:
            return
        if ict.b_ope1:
            ict.b_ope2 = value
            return
        if not ict.b_ope1:
            ict.b_ope1 = value
            return
        if ict.b_ope2:
            raise RuntimeError('Many PostKey : Boundary_Operator')

class SearchShippingQuery:
    word :str = ""
    pref :str = ""
    errmsg :str = ""

    def __init__(self,
                 word :str = "",
                 pref :str = "",
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
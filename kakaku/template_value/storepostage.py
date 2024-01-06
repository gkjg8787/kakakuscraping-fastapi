from typing import List
from enum import Enum
import re

from common import (
    const_value,
    templates_string,
)
from itemcomb import postage_data as posd

class BoundaryConverter:
    CONVEERT_TABLE = {posd.BoundaryOperator.GE.operator:posd.BoundaryOperator.GE.jtext,
                      posd.BoundaryOperator.LE.operator:posd.BoundaryOperator.LE.jtext,
                      posd.BoundaryOperator.GT.operator:posd.BoundaryOperator.GT.jtext,
                      posd.BoundaryOperator.LT.operator:posd.BoundaryOperator.LT.jtext,
                      ":":" かつ "
                     }
    @classmethod
    def convert_boundary_to_jtext(cls, boundary :str):
        target = boundary
        for bef, aft in cls.CONVEERT_TABLE.items():
            target = re.sub(bef, aft, target)
        return target

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
        if opestr == posd.BoundaryOperator.GE.operator:
            res.ge = selected
            return res
        if opestr == posd.BoundaryOperator.GT.operator:
            res.gt = selected
            return res
        if opestr == posd.BoundaryOperator.LE.operator:
            res.le = selected
            return res
        if opestr == posd.BoundaryOperator.LT.operator:
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
    store_id :int | str
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
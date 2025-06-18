from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import copy
from datetime import datetime

from pydantic import BaseModel

from common import const_value


class ParseItemInfo(BaseModel):
    id: int | None = None
    name: str = ""
    newPrice: int = const_value.INIT_PRICE
    usedPrice: int = const_value.INIT_PRICE
    condition: str = ""
    taxin: bool = False
    onSale: bool = False
    saleName: str = ""
    timeStamp: datetime | None = None
    isSuccess: bool = False
    url: str = ""  # | None = None
    oldPrice: int = const_value.INIT_PRICE
    storename: str = ""
    inventoryCount: int = 0

    def getOrderedDict(self):
        return OrderedDict(
            [
                ("url_id", self.id),
                ("created_at", self.timeStamp),
                ("uniqname", self.name),
                ("usedprice", self.usedPrice),
                ("newprice", self.newPrice),
                ("taxin", self.taxin),
                ("onsale", self.onSale),
                ("salename", self.saleName),
                ("issuccess", self.isSuccess),
                ("storename", self.storename),
                ("oldprice", self.oldPrice),
                ("trendrate", self.getTrendRate()),
            ]
        )

    def hasPrice(self):
        npn = self.newPrice
        upn = self.usedPrice
        if npn < 0 and upn < 0:
            return False
        return True

    def getLowestPrice(self):
        np = int(self.newPrice)
        up = int(self.usedPrice)
        if np < 0:
            return up
        if up < 0:
            return np
        if np > up:
            return up
        else:
            return np

    def getTrendRate(self):
        hasPriceflg = self.hasPrice()
        if not hasPriceflg:
            return 0
        lpn = self.getLowestPrice()
        opn = int(self.oldPrice)
        if lpn <= 0 or opn <= 0:
            return 0
        rate = int(lpn) / int(opn)
        return rate - 1


class ParsePostageTerms:
    boundary: str = ""
    postage: int = 0


class ParseStorePostage:
    storename: str = ""
    terms: list[ParsePostageTerms] = []
    campaign_msg: str = ""
    target_prefectures: list[str] = []

    def __init__(self):
        pass

    def add_terms(self, terms: ParsePostageTerms):
        if not self.terms:
            self.terms = [terms]
            return
        self.terms.append(terms)

    def set_prefectures(self, prefecture_list: list[str]):
        self.target_prefectures = copy.deepcopy(prefecture_list)


class ParseShopIDInfo:
    storename: str = ""
    shop_id: int = const_value.NONE_ID
    url: str = ""


class ParseItems(metaclass=ABCMeta):
    @abstractmethod
    def getItems(self):
        return ()

    @classmethod
    def trimStr(cls, text: str):
        table = str.maketrans(
            {
                "\u3000": "",
                "\r": "",
                "\n": "",
                "\t": " ",
                "\xa0": " ",
            }
        )
        return text.translate(table).strip()

    def hasPostage(self) -> bool:
        return False

    def getPostageList(self) -> list[ParseStorePostage] | None:
        return None

    def hasShopIDInfo(self) -> bool:
        return False

    def getShopIDInfo(self) -> dict[str, ParseShopIDInfo] | None:
        return None

    def isDeleted(self) -> bool:
        return False

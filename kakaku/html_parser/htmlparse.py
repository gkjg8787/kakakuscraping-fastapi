from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import copy

from common import const_value


class ParseItemInfo:
    def __init__(self):
        self.__id = None
        self.__name = ""
        self.__newPrice = const_value.INIT_PRICE
        self.__usedPrice = const_value.INIT_PRICE
        self.__taxin = False
        self.__onSale = False
        self.__saleName = ""
        self.__timeStamp = None
        self.__isSuccess = False
        self.__url = None
        self.__oldPrice = const_value.INIT_PRICE
        self.__storename = ""

    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, id):
        self.__id = id

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def newPrice(self):
        return self.__newPrice

    @newPrice.setter
    def newPrice(self, newPrice):
        self.__newPrice = newPrice

    @property
    def usedPrice(self):
        return self.__usedPrice

    @usedPrice.setter
    def usedPrice(self, usedPrice):
        self.__usedPrice = usedPrice

    @property
    def taxin(self):
        return self.__taxin

    @taxin.setter
    def taxin(self, taxin):
        self.__taxin = taxin

    @property
    def onSale(self):
        return self.__onSale

    @onSale.setter
    def onSale(self, onSale):
        self.__onSale = onSale

    @property
    def saleName(self):
        return self.__saleName

    @saleName.setter
    def saleName(self, saleName):
        self.__saleName = saleName

    @property
    def timeStamp(self):
        return self.__timeStamp

    @timeStamp.setter
    def timeStamp(self, timeStamp):
        self.__timeStamp = timeStamp

    @property
    def isSuccess(self):
        return self.__isSuccess

    @isSuccess.setter
    def isSuccess(self, isSuccess):
        self.__isSuccess = isSuccess

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, url):
        self.__url = url

    @property
    def oldPrice(self):
        return self.__oldPrice

    @oldPrice.setter
    def oldPrice(self, oldPrice):
        self.__oldPrice = oldPrice

    @property
    def storename(self):
        return self.__storename

    @storename.setter
    def storename(self, storename):
        self.__storename = storename

    def getOrderedDict(self):
        return OrderedDict(
            [
                ("url_id", self.__id),
                ("created_at", self.__timeStamp),
                ("uniqname", self.__name),
                ("usedprice", self.__usedPrice),
                ("newprice", self.__newPrice),
                ("taxin", self.__taxin),
                ("onsale", self.__onSale),
                ("salename", self.__saleName),
                ("issuccess", self.__isSuccess),
                ("storename", self.__storename),
                ("oldprice", self.__oldPrice),
                ("trendrate", self.getTrendRate()),
            ]
        )

    def getName(self):
        return self.name

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
        table = str.maketrans({"\u3000": "", "\r": "", "\n": "", "\t": " "})
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

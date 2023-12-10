from enum import Enum, auto, unique

class AutoUpperName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.upper()

class AutoLowerName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

class FilterQueryName(AutoLowerName):
    GID = auto()
    ACT = auto()
    STORE = auto()
    ISORT = auto()
    CATEGORY = auto()
    PAGE = auto()
    WORD = auto()
    SAFES = auto()
    ZAIKO = auto()
    LISTVIEW = auto()
    PREF = auto()
    USORT = auto()
    EX_STORE = auto()
    ESSORT = auto()
    PRMIN = auto()
    PRMAX = auto()

@unique
class ActFilterName(Enum):
    ALL = (1, "全て")
    ACT = (2, "ACTIVEのみ")
    INACT = (3, "INACTIVEのみ")
    
    def __init__(self, id:int, text:str):
        self.id = id
        self.text = text

    @classmethod
    def hasValue(cls, value) -> bool:
        for a in cls:
            if a.id == value:
                return True
        return False
@unique
class ItemSortName(Enum):
    OLD_ITEM = (1, "登録が古い",)
    NEW_ITEM = (2, "登録が新しい",)
    LOW_PRICE = (3, "値段が安い",)
    HIGH_PRICE = (4, "値段が高い",)
    ITEM_NAME = (5, "アイテム名",)
    STORE_NAME = (6, "店名",)
    LOW_TRENDRATE = (7, "値下げ",)
    HIGH_TRENDRATE = (8, "値上げ",)
    OLD_UPDATE_TIME = (9, "更新が古い")
    NEW_UPDATE_TIME = (10, "更新が新しい")
    LOW_LOWESTPRICE = (11, "最安値が安い")
    HIGH_LOWESTPRICE = (12, "最安値が高い")
    CLOSEST_LOWESTPRICE = (13, "最安値との差が小さい")
    FURTHEST_LOWESTPRICE = (14, "最安値との差が大きい")

    def __init__(self, id:int, text:str):
        self.id = id
        self.qname = self.name.lower()
        self.jname = text
    
    @classmethod
    def hasId(cls, id:int) -> bool:
        for isn in cls:
            if isn.id == id:
                return True
        return False

@unique
class ExtractStoreSortName(Enum):
    OLD_ITEM = (1, "登録が古い",)
    NEW_ITEM = (2, "登録が新しい",)
    LOW_PRICE = (3, "値段が安い",)
    HIGH_PRICE = (4, "値段が高い",)
    ITEM_NAME = (5, "アイテム名",)
    LOW_TRENDRATE = (7, "値下げ",)
    HIGH_TRENDRATE = (8, "値上げ",)
    OLD_UPDATE_TIME = (9, "更新が古い")
    NEW_UPDATE_TIME = (10, "更新が新しい")
    LOW_LOWESTPRICE = (11, "最安値が安い")
    HIGH_LOWESTPRICE = (12, "最安値が高い")
    CLOSEST_LOWESTPRICE = (13, "最安値との差が小さい")
    FURTHEST_LOWESTPRICE = (14, "最安値との差が大きい")

    def __init__(self, id:int, text:str):
        self.id = id
        self.qname = self.name.lower()
        self.jname = text
    
    @classmethod
    def hasId(cls, id:int) -> bool:
        for isn in cls:
            if isn.id == id:
                return True
        return False

@unique
class UrlSortName(Enum):
    URLID_ASC = (1, "URL_ID昇順",)
    URLID_DESC = (2, "URL_ID降順",)
    ITEMID_ASC = (3, "ITEM_ID昇順",)
    ITEMID_DESC = (4, "ITEM_ID降順",)

    def __init__(self, id:int, text:str):
        self.id = id
        self.qname = self.name.lower()
        self.jname = text
    
    @classmethod
    def hasId(cls, id:int) -> bool:
        for isn in cls:
            if isn.id == id:
                return True
        return False

class TemplatePostName(AutoLowerName):
    ITEM_ID = auto()
    ITEM_NAME = auto()
    URL_PATH = auto()
    URL_ID = auto()
    GROUP_ID = auto()
    GROUP_NAME = auto()
    GROUP_ITEM_LIST = auto()
    SEARCH_QUERY = auto()
    ITEM_ALL_UPDATE = auto()
    RETURN_USER = auto()
    STORE_NAME = auto()
    STORE_ID = auto()

class ItemDetailQueryName(AutoLowerName):
    ITEMID = auto()

class ItemDetailConst(Enum):
    YEARS_LIMIT = 1
    MAX_LIMIT = 100

class FilterDefault:
    GID = -1
    PAGE = 1
    STORES_SEARCH = []
    CATEGORY = 0
    SAFE_SEARCH = 1
    ZAIKO = 0
    LIST_VIEW = 0

class ItemUpdateValue:
    ITEM_ALL_UPDATE = "一括情報取得"

class FilterOnOff:
    ON = 1
    OFF = 0

class SearchConst:
    WORD_MAX_LENGTH = 256

class DashBoardPostName(AutoLowerName):
    SYSTEM_CTRL_BTN = auto()

class SystemCtrlBtnName(AutoLowerName):
    STARTUP = auto()
    STOP = auto()
    RESTART = auto()

class ItemCombPostKey:
    TERMS = 'terms'
    BOUNDARY = 'boundary'
    OPE = 'b_ope'
    POSTAGE = 'postage'
    STORENAME = 'store_name'

class AnalysisQueryName(AutoLowerName):
    ATID = auto()

@unique
class AnalysisTermName(Enum):
    ONE_WEEK = (1, "１週間",)
    TWO_WEEK = (2, "２週間",)
    ONE_MONTH = (3, "１か月",)
    THREE_MONTH = (4, "３か月",)
    SIX_MONTH = (5, "６か月",)
    ONE_YEAR = (6, "１年",)

    def __init__(self, id:int, text:str):
        self.id = id
        self.qname = self.name.lower()
        self.jname = text
    
    @classmethod
    def hasId(cls, id:int) -> bool:
        for isn in cls:
            if isn.id == id:
                return True
        return False
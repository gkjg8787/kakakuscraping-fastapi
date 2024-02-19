import re
from urllib.parse import urlencode

from url_search import readoption


class SurugayaURL:
    def __init__(self, rsopts: readoption.ReadSearchOpt):
        self.base = "https://www.suruga-ya.jp/search"
        self.query = {
            "category": "",
            "search_word": "",
            "is_marketplace": 0,
            "ch": "true",
            "inStock": "On",
        }
        self.rsopts = rsopts
        self.isExistCate = True

    def setParameter(self, param: dict):
        self.isExistCate = True
        if "category" in param:
            opts = self.rsopts.getOptions()
            idtable = opts["category"]["surugaya"]["idtable"]
            self.inCategoryTable(idtable, str(param["category"]))

        if "page" in param:
            try:
                num = int(param["page"])
                if num > 0:
                    self.setPage(num)
            except ValueError:
                pass

        if "zaiko" in param:
            try:
                num = int(param["zaiko"])
                if num == 1:
                    self.setStock("Off")
            except ValueError:
                pass

    def setStock(self, val):
        self.query["inStock"] = val

    def setPage(self, num):
        self.query["page"] = num

    def inCategoryTable(self, table: dict, val):
        if val not in table:
            self.isExistCate = False
            return
        num = table[val]
        if len(num) != 0:
            self.setCategory(num)

    def setCategory(self, num):
        self.query["category"] = num

    def setMarketPlace(self, num):
        self.query["is_marketplace"] = num

    def setWord(self, word):
        self.query["search_word"] = word

    def createURL(self):
        url = "%s?%s" % (self.base, urlencode(self.query))
        return url

    def isExistCategory(self):
        return self.isExistCate


class SurugayaPurchaseURL:
    domain = "https://www.suruga-ya.jp"
    individual_url = f"{domain}/kaitori/kaitori_detail/"
    search_url = f"{domain}/kaitori/search_buy"
    word: str = ""
    surugaya_item_id: str = ""

    @classmethod
    def is_my_domain(cls, urlpath: str):
        return cls.domain in urlpath

    @classmethod
    def get_url(cls, urlpath: str, search_word: str = ""):
        surugaya_id = cls.parse_surugaya_id(urlpath=urlpath)
        if surugaya_id:
            return cls.individual_url + str(surugaya_id)

        options = {
            "category": "",
            "search_word": search_word,
        }
        return "%s?%s" % (cls.search_url, urlencode(options))

    @classmethod
    def parse_surugaya_id(cls, urlpath: str) -> str:
        if not cls.is_my_domain(urlpath=urlpath):
            return ""
        ptn = r"(other|detail)/([0-9]+)"
        m = re.search(ptn, urlpath)
        if m:
            return m[2]
        return ""

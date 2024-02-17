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
    individual_url = "https://www.suruga-ya.jp/kaitori/kaitori_detail/"
    search_url = "https://www.suruga-ya.jp/kaitori/search_buy"
    word: str = ""
    surugaya_item_id: str = ""

    def __init__(self, word: str = "", surugaya_item_id: str = ""):
        if word and surugaya_item_id:
            raise ValueError("only one of word or surugaya_item_id")
        if not word and not surugaya_item_id:
            raise ValueError("parameter is none")
        if word:
            self.word = word.strip()
        if surugaya_item_id:
            self.surugaya_item_id = surugaya_item_id.strip()

    def createURL(self):
        if self.word:
            options = {
                "category": "",
                "search_word": self.word,
            }
            return "%s?%s" % (self.search_url, urlencode(options))
        if self.surugaya_item_id:
            return self.individual_url + str(self.surugaya_item_id)
        return ""

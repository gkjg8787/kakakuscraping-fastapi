from urllib.parse import urlencode


class NetoffURL:
    def __init__(self, rsopts):
        self.base = "https://www.netoff.co.jp/cmdtyallsearch/"
        self.query = {"word": "", "cname": ""}
        self.rsopts = rsopts
        self.isExistCate = True

    def setParameter(self, param):
        self.isExistCate = True
        if "category" in param:
            opts = self.rsopts.getOptions()
            idtable = opts["category"]["netoff"]["idtable"]
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
                    self.setStock(num)
            except ValueError:
                pass

    def setStock(self, num):
        self.query["stock"] = num

    def setPage(self, num):
        self.query["page"] = num
        if num > 1:
            self.query["cl"] = (num - 1) * 100

    def inCategoryTable(self, table, val):
        if val not in table:
            self.isExistCate = False
            return
        num = table[val]
        if len(num) != 0:
            self.setCategory(num)

    def setCategory(self, num):
        self.query["cat"] = num

    def setWord(self, word):
        self.query["word"] = word

    def createURL(self):
        url = "%s?%s" % (self.base, urlencode(self.query))
        return url

    def isExistCategory(self):
        return self.isExistCate

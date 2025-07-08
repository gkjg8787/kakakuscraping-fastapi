from . import htmlparse


class ParseItemsForPriceUpdate(htmlparse.ParseItems):
    parseiteminfos: list[htmlparse.ParseItemInfo]

    def __init__(self, parseiteminfos: list[htmlparse.ParseItemInfo]):
        if not parseiteminfos:
            self.parseiteminfos = []
            return
        self.parseiteminfos = [p for p in parseiteminfos]

    def add_parseiteminfo(self, pii: htmlparse.ParseItemInfo):
        self.parseiteminfos.append(pii)

    def getItems(self):
        return tuple(self.parseiteminfos)

    def get_url(self):
        if not self.parseiteminfos:
            return ""
        return self.parseiteminfos[0].url

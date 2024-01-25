from abc import ABCMeta


class SiteSearchOpt(metaclass=ABCMeta):
    def __init__(self):
        self.name = ""
        self.site = None
        self.parser = None
        self.requestOpt = None

    def getName(self):
        return self.name

    def setSearchWord(self, word):
        pass

    def getSite(self):
        return self.site

    def getParser(self):
        return self.parser

    def getRequestOpt(self):
        return self.requestOpt

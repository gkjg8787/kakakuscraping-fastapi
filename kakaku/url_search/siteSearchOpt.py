from abc import ABCMeta
from downloader import requestoption
from html_parser.search_parser import SearchParser
from .urlcreator import URLCreator


class SiteSearchOpt(metaclass=ABCMeta):
    name: str
    site: URLCreator
    parser: SearchParser
    requestOpt: requestoption

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

    def setParamOpt(self, paramopt):
        pass

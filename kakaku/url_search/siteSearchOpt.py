from abc import ABCMeta, abstractmethod
from downloader import requestoption
from html_parser.search_parser import SearchParser
from .urlcreator import URLCreator


class SiteSearchOpt(metaclass=ABCMeta):
    name: str
    site: URLCreator
    parser: SearchParser
    requestOpt: requestoption

    def getName(self):
        return self.name

    @abstractmethod
    def setSearchWord(self, word):
        """検索ワードを設定する抽象メソッド"""

    def getSite(self):
        return self.site

    def getParser(self):
        return self.parser

    def getRequestOpt(self):
        return self.requestOpt

    @abstractmethod
    def setParamOpt(self, paramopt):
        """検索オプションを設定する抽象メソッド"""

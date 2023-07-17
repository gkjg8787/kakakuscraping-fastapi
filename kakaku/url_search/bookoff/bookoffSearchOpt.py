from url_search import siteSearchOpt
from url_search.bookoff import bookoffURL
from downloader import requestoption
from html_parser import bookoff_search



class BookoffSearchOpt(siteSearchOpt.SiteSearchOpt):

    def __init__(self, confopt):
        self.name = 'bookoff'
        self.confopt = confopt
        self.site = bookoffURL.BookoffURL(confopt)
        self.requestOpt = requestoption.RequestOpt()
        self.parser = bookoff_search.SearchBookoff()

    
    def setSearchWord(self, word):
        self.site.setWord(word)
    
    def setParamOpt(self, paramopt):
        self.site.setParameter(paramopt)

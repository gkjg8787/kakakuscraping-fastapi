import os
from url_search import siteSearchOpt
from url_search.surugaya import surugayaURL
from downloader import requestoption
from html_parser import surugaya_search

from common import read_config
from common.filter_name import FilterQueryName

class SurugayaSearchOpt(siteSearchOpt.SiteSearchOpt):
    COOKIE_FNAME = 'surugaya_safeoff_cookie.lwp'

    def __init__(self, confopt):
        self.name = 'surugaya'
        self.confopt = confopt
        self.site = surugayaURL.SurugayaURL(confopt)
        self.requestOpt = requestoption.RequestOpt()
        self.parser = surugaya_search.SearchSurugaya()
    
    def setSearchWord(self, word):
        self.site.setWord(word)

    def setParamOpt(self, paramopt):
        self.site.setParameter(paramopt)
        self.setSafeSearchParam(paramopt)
    
    def setSafeSearchParam(self, paramopt):
        if not FilterQueryName.SAFES.value in paramopt: return
        
        num = -1
        try:
            num = int(paramopt[FilterQueryName.SAFES.value])
        except:
            pass
        if num == 0:
            fpath = os.path.join(read_config.get_search_option_path(), "surugaya", SurugayaSearchOpt.COOKIE_FNAME)
            self.requestOpt.setCookieFilePath(fpath)
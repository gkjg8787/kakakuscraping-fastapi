import os
from url_search import siteSearchOpt
from url_search.netoff import netoffURL
from downloader import requestoption
from html_parser import netoff_search

from common import read_config
from common.filter_name import FilterQueryName

class NetoffSearchOpt(siteSearchOpt.SiteSearchOpt):
    COOKIE_FNAME = 'netoff_safeoff_cookie.lwp'

    def __init__(self, confopt):
        self.name = 'netoff'
        self.confopt = confopt
        self.site = netoffURL.NetoffURL(confopt)
        self.requestOpt = requestoption.RequestOpt()
        self.parser = netoff_search.SearchNetoff()
    
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
            fpath = os.path.join(read_config.get_search_option_path(), "netoff",NetoffSearchOpt.COOKIE_FNAME)
            self.requestOpt.setCookieFilePath(fpath)
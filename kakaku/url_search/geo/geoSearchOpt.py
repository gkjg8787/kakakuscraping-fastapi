from url_search import siteSearchOpt
from url_search.geo import geoURL
from downloader import requestoption
from html_parser import geo_search


class GeoSearchOpt(siteSearchOpt.SiteSearchOpt):

    def __init__(self, confopt):
        self.name = 'geo'
        self.confopt = confopt
        self.site = geoURL.GeoURL(confopt)
        self.requestOpt = requestoption.RequestOpt()
        self.parser = geo_search.SearchGeo()
    
    def setSearchWord(self, word):
        self.site.setWord(word)
    
    def setParamOpt(self, paramopt):
        self.site.setParameter(paramopt)

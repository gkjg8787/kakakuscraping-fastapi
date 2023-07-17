import sys
import json
import queue

from typing import Dict, List

from downloader import download_html
from html_parser.search_parser import SearchCmn, SearchParser
from url_search import readoption
from common.filter_name import SearchConst, FilterQueryName

from common import cmnlog
from url_search.siteSearchOpt import SiteSearchOpt
from url_search.surugaya import surugayaSearchOpt
from url_search.netoff import netoffSearchOpt
from url_search.bookoff import bookoffSearchOpt
from url_search.geo import geoSearchOpt


from cache import getcache

import logging
from multiprocessing import Process, Manager
import gzip


QUEUE_TIMEOUT = 10

def getLogger():
    logname = cmnlog.LogName.SEARCH
    return cmnlog.getLogger(logname)

def deleteLogger():
    logname = cmnlog.LogName.SEARCH
    return cmnlog.deleteLogger(logname)

def getCacheKey(sword, optjson):
    key = sword
    if not optjson is None:
        jsontext = json.dumps(optjson)
        key += " " + jsontext
    return key

def getCache(sword, optjson):
    if getcache.isSearchCacheFunc():
        key = getCacheKey(sword, optjson)
        text = getcache.getSearchCache().read(key)
        return text
    return ""

def setCache(sword, optjson, text):
    if getcache.isSearchCacheFunc():
        key = getCacheKey(sword, optjson)
        getcache.getSearchCache().write(key, text)
    return

def getSearch(sword, optjson=None):
    cache = getCache(sword, optjson)
    if len(cache) > 0:
        return json.loads(cache)
    si = SearchItem(sword, optjson)
    si.start()
    res = { SearchParser.ITEMS : si.getItems() , SearchParser.PAGE : si.getPageInfo() }
    setCache(sword, optjson, json.dumps(res))
    return res

def createOption(sword, optjson=None):
    sopt = SearchOpt(sword)
    sopt.setParamOpt(optjson)
    return sopt

def outputCompress(text, optjson=None):
    logger = getLogger()
    if len(text) == 0:
        logger.error(__file__ + ' no text no output')
        print('')
        return

    if optjson is None\
        or not 'output' in optjson \
        or not 'type' in optjson['output'] \
        or not optjson['output']['type'] == 'gzip':
        print(text)
        return

    logger.debug(__file__ + ' output gzip')
    btext = text.encode(encoding='utf-8')
    gzipret = gzip.compress(btext)
    sys.stdout.buffer.write(gzipret)


def get_search_for_inner(sword :str, optdict = None) -> dict:
    ERR_KEY = "errmsg"
    errmsg = ""
    RESULT_KEY = "result"

    deleteLogger()
    cmnlog.createLogger(cmnlog.LogName.SEARCH)
    logger = getLogger()
    logger.setLevel(logging.DEBUG)
    logger.info(__file__ + ' start url_search')

    logger.info(__file__ + " sword=" + sword)
    if len(sword) > SearchConst.WORD_MAX_LENGTH:
        errmsg = f"parameter error p1 more_then_max length={len(sword)}"
        return {ERR_KEY:errmsg}
    
    if optdict:
        logger.info(__file__ + ' optparam='+json.dumps(optdict))

    logger.debug(__file__ + ' start Search')
    res = getSearch(sword, optdict)
    logger.debug(__file__ + ' end Search')
    logger.info(__file__ + ' end url_search')
    return {RESULT_KEY:res}


def start_cmd():
    argslen = len(sys.argv)
    maxlen = 512
    cmnlog.createLogger(cmnlog.LogName.SEARCH)
    logger = getLogger()
    logger.setLevel(logging.DEBUG)
    logger.info(__file__ + ' start searchcmd')

    if argslen < 2 or argslen > 3:
        print("ERROR PARAMETER_NUM")
        logger.error(__file__ + ' parameter error length=' + str(argslen))
        sys.exit()
    
    logger.info(__file__ + ' sword='+sys.argv[1])
    if len(sys.argv[1]) > maxlen:
        print("ERROR PARAMTER_LENGTH")
        logger.error(__file__ + ' parameter error p1 more_then_max length=' + str(len(sys.argv[1])))
        sys.exit()

    optjson = None
    if argslen == 3:
        # option
        if len(sys.argv[2]) > maxlen:
            print("ERROR PARAMETER_LENGTH")
            logger.error(__file__ + ' parameter error p2 more_then_max length=' + str(len(sys.argv[2])))
            sys.exit()
        logger.info(__file__ + ' optparam='+sys.argv[2])
        optjson = json.loads(sys.argv[2])
    
    logger.debug(__file__ + ' start Search')
    text = getSearch(sys.argv[1], optjson)
    logger.debug(__file__ + ' end Search')
    outputCompress(text, optjson)
    logger.debug(__file__ + ' print Search Result')
    logger.debug(__file__ + ' end searchcmd')

class SearchProcResult:
    def __init__(self):
        self.items = {}
        self.htmlpart = ''
        self.pageinfo = {}
    
    def setItems(self, items):
        self.items = items
    
    def getItems(self):
        return self.items
    
    def setHtmlPart(self, htmlp):
        self.htmlpart = htmlp
    
    def addHtmlPart(self, htmlp):
        self.htmlpart += htmlp
    
    def getHtmlPart(self):
        return self.htmlpart
    
    def setPageInfo(self, pageinfo):
        self.pageinfo = pageinfo
    
    def getPageInfo(self):
        return self.pageinfo

class SearchItem:
    def __init__(self, sword, optjson=None):
        self.sopt = self.createOption(sword, optjson)
    
    def createOption(self, sword, optjson=None):
        sopt = SearchOpt(sword)
        sopt.setParamOpt(optjson)
        return sopt

    def start(self):
        self.allitems = []
        self.pageinfo = None
        pageinfo = { SearchCmn.ENABLE : SearchCmn.FALSE }
        sopt = self.sopt
        self.setCurrentPage(pageinfo, sopt.getParamOpt())
        
        logger = getLogger()
        logger.debug(__file__ + ' start SearchItem')
        m = Manager()
        retq = m.Queue()
        taskq = m.Queue()
        procs = []
        waittime = QUEUE_TIMEOUT
        for sitename in sopt.targetstore:
            searcho = sopt.getSiteSearch(sitename)
            taskq.put(searcho)
            proc = Process(target=self.searchResult, args=(taskq, retq, waittime))
            proc.start()
            procs.append(proc)
            
        for proc in procs:
            proc.join()

        for i in range(len(procs)):
            try:
                spr :SearchProcResult = retq.get(timeout=waittime)
                self.allitems.extend(spr.getItems())
                self.setPage(pageinfo, spr.getPageInfo())
                self.pageinfo = pageinfo
            except queue.Empty:
                logger.error('{}  [{}] retqueue timeout'.format(__file__ ,str(i)))

        if SearchCmn.TRUE != pageinfo[SearchCmn.ENABLE]:
            logger.debug(__file__ + ' end SearchItem')
            return
        
        #logger.debug(__file__ + ' page decorate')
        #pd = PageDeco()
        #pd.setPage(pageinfo, sopt.getParamOpt())
        #self.htmlparts += '\n' + pd.getHtml() + '\n'
        logger.debug(__file__ + ' end SearchItem')
    
    def setCurrentPage(self, pageinfo, urlparam):
        if not SearchCmn.PAGE in urlparam:
            pageinfo[SearchCmn.CURRENT] = '1'
            return
        pageinfo[SearchCmn.CURRENT] = urlparam[SearchCmn.PAGE]

    def searchResult(self, taskq , retq, wtime :int):
        logger = getLogger()
        try:
            searcho :SiteSearchOpt = taskq.get(timeout=wtime)
        except queue.Empty:
            logger.error(__file__ + ' taskqueue timeout')
            retq.put(spr)
            return
        spr = SearchProcResult()
        site = searcho.getSite()
        if not site.isExistCategory():
            logger.info('{} {} {}'.format(__file__, searcho.getName(), ' no exist category'))
            retq.put(spr)
            return
        retbool, html = self.downloadHtml(searcho, logger)
        if not retbool:
            logger.error(__file__ + ' fail download')
            retq.put(spr)
            return
        self.parseHtml(searcho, logger, spr, html)
        retq.put(spr)

    def downloadHtml(self, searcho :SiteSearchOpt, logger):
        site = searcho.getSite()
        dlopt = searcho.getRequestOpt()
        logger.debug(__file__ + ' start DownLoad')
        retbool, html = download_html.getUrlHtml(
                            site.createURL()
                            ,dlopt )
        logger.debug(__file__ + ' end DownLoad')
        return retbool, html
    
    def parseHtml(self, searcho :SiteSearchOpt, logger , spr :SearchProcResult, html :str):
        logger.debug(__file__ + ' start item parse')
        parser = searcho.getParser()
        parser.parseSearch(html)
        logger.debug(__file__ + ' end item parse')
        items = parser.getItems()
        spr.setItems(items)
        if len(items) > 0:
            logger.debug(__file__ + ' start page parse')
            spr.setPageInfo(parser.getPage())
            logger.debug(__file__ + ' end page parse')
        """
        if len(items) > 0 :
            logger.debug(__file__ + ' start decorate')
            deco = searcho.getDecorator()
            deco.setItems(items)
            spr.setHtmlPart(deco.getHtml() + '\n')
            spr.setPageInfo(parser.getPage())
            logger.debug(__file__ + ' end decorate')
            """

    def setPage(self, pageinfo, searchret):
        if searchret is None : return
        if not SearchCmn.ENABLE in searchret: return
        if not SearchCmn.TRUE == searchret[SearchCmn.ENABLE] : return

        pageinfo[SearchCmn.ENABLE] = SearchCmn.TRUE
        MAX = SearchCmn.MAX
        MIN = SearchCmn.MIN

        if not MAX in pageinfo:
            pageinfo[MAX] = int(searchret[MAX])
        elif int(pageinfo[MAX]) < int(searchret[MAX]):
            pageinfo[MAX] = int(searchret[MAX])

        if not MIN in pageinfo:
            pageinfo[MIN] = int(searchret[MIN])
        elif int(pageinfo[MIN]) > int(searchret[MIN]):
            pageinfo[MIN] = int(searchret[MIN])
        
        if SearchCmn.MOREPAGE in searchret:
            pageinfo[SearchCmn.MOREPAGE] = SearchCmn.TRUE


    def getPageInfo(self):
        return self.pageinfo
    
    def getItems(self):
        return self.allitems



class SearchOpt:
    SURUGAYA = 'surugaya'
    BOOKOFF = 'bookoff'
    NETOFF = 'netoff'
    GEO = 'geo'
    def __init__(self, word):
        self.confopts = readoption.ReadSearchOpt()
        self.searchs :Dict[str, SiteSearchOpt]= { SearchOpt.SURUGAYA : surugayaSearchOpt.SurugayaSearchOpt(self.confopts)
                        ,SearchOpt.NETOFF : netoffSearchOpt.NetoffSearchOpt(self.confopts)
                        ,SearchOpt.BOOKOFF : bookoffSearchOpt.BookoffSearchOpt(self.confopts)
                        ,SearchOpt.GEO : geoSearchOpt.GeoSearchOpt(self.confopts)
                        }
        self.targetstore = []
        self.urlparam = { FilterQueryName.WORD.value : word} 
        self.supportSite = [ SearchOpt.SURUGAYA
                            ,SearchOpt.NETOFF
                            ,SearchOpt.BOOKOFF
                            ,SearchOpt.GEO
                             ]

        self.setWord(word)
    
    def setWord(self, word):
        for search in self.searchs.values():
            search.setSearchWord(word)
    
    def getSearchWord(self):
        return self.urlparam[FilterQueryName.WORD.value]
    
    def getParamOpt(self):
        return self.urlparam

    def setParamOpt(self, paramopt):
        self.createTarget(paramopt)
        if paramopt is None: return

        self.urlparam.update(paramopt)
        for sitename in self.searchs:
            self.searchs[sitename].setParamOpt(paramopt)
    
    def createTarget(self, paramopt):
        logger = getLogger()
        if paramopt is None or not 'store' in paramopt:
            self.targetstore = self.supportSite
            logger.debug(__file__ + ' no store option')
            return
        ropt = self.confopts.getOptions()
        for storeid in paramopt['store']:
            if not str(storeid) in ropt['store']: continue
            
            sname = ropt['store'][str(storeid)]['name']
            
            if not sname in self.supportSite: continue

            self.targetstore.append(sname)
    
    def getSiteSearch(self, name):
        return self.searchs[name]
    
    def getSite(self, name):
        return self.searchs[name].getSite()
    
    def getRequestOpt(self, name):
        return self.searchs[name].getRequestOpt()
    
    def getParser(self, name):
        return self.searchs[name].getParser()



if __name__ == '__main__':
    start_cmd()


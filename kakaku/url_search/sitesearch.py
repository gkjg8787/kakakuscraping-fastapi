import json
import queue

from downloader import download_html
from html_parser.search_parser import SearchCmn, SearchParser
from url_search import readoption
from common.filter_name import SearchConst, FilterQueryName

from common import cmnlog
from url_search.siteSearchOpt import SiteSearchOpt
from url_search.surugaya import surugayaSearchOpt
from url_search.netoff import netoffSearchOpt
from url_search.bookoff import bookoffSearchOpt


from cache import getcache

import logging
from multiprocessing import Process, Manager


QUEUE_TIMEOUT = 10


def getLogger():
    logname = cmnlog.LogName.SEARCH
    return cmnlog.getLogger(logname)


def getCacheKey(sword: str, optjson: dict | None):
    key = sword
    if optjson is not None:
        jsontext = json.dumps(optjson)
        key += " " + jsontext
    return key


def getCache(sword: str, optjson: dict | None):
    if getcache.isSearchCacheFunc():
        key = getCacheKey(sword, optjson)
        text = getcache.getSearchCache().read(key)
        return text
    return ""


def setCache(sword: str, optjson: dict | None, text: str):
    if getcache.isSearchCacheFunc():
        key = getCacheKey(sword, optjson)
        getcache.getSearchCache().write(key, text)
    return


def getSearch(sword: str, optjson: dict | None = None) -> dict:
    cache = getCache(sword, optjson)
    if len(cache) > 0:
        return json.loads(cache)
    si = SearchItem(sword, optjson)
    si.start()
    res = {SearchParser.ITEMS: si.getItems(), SearchParser.PAGE: si.getPageInfo()}
    setCache(sword, optjson, json.dumps(res))
    return res


def get_search_for_inner(sword: str, optdict: dict | None = None) -> dict:
    ERR_KEY = "errmsg"
    errmsg = ""
    RESULT_KEY = "result"

    logger = getLogger()
    logger.setLevel(cmnlog.LOGGING_LEVEL)
    logger.info(__file__ + " start url_search")

    logger.info(f"{__file__} sword={sword}")
    if len(sword) > SearchConst.WORD_MAX_LENGTH:
        errmsg = f"parameter error p1 more_then_max length={len(sword)}"
        return {ERR_KEY: errmsg}

    if optdict:
        logger.info(__file__ + " optparam=" + json.dumps(optdict))

    logger.debug(__file__ + " start Search")
    res = getSearch(sword, optdict)
    logger.debug(__file__ + " end Search")
    logger.info(__file__ + " end url_search")
    return {RESULT_KEY: res}


class SearchProcResult:
    items: dict
    htmlpart: str
    pageinfo: dict

    def __init__(self):
        self.items = {}
        self.htmlpart = ""
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


class SearchOpt:
    SURUGAYA = "surugaya"
    BOOKOFF = "bookoff"
    NETOFF = "netoff"

    confopts: readoption.ReadSearchOpt
    searchs: dict[str, SiteSearchOpt]
    targetstore: list[str]
    urlparam: dict
    supportSite: list[str]

    def __init__(self, word):
        self.confopts = readoption.ReadSearchOpt()
        self.searchs: dict[str, SiteSearchOpt] = {
            SearchOpt.SURUGAYA: surugayaSearchOpt.SurugayaSearchOpt(self.confopts),
            SearchOpt.NETOFF: netoffSearchOpt.NetoffSearchOpt(self.confopts),
            SearchOpt.BOOKOFF: bookoffSearchOpt.BookoffSearchOpt(self.confopts),
        }
        self.targetstore = []
        self.urlparam = {FilterQueryName.WORD.value: word}
        self.supportSite = [
            SearchOpt.SURUGAYA,
            SearchOpt.NETOFF,
            SearchOpt.BOOKOFF,
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
        if paramopt is None:
            return

        self.urlparam.update(paramopt)
        for sitename in self.searchs:
            self.searchs[sitename].setParamOpt(paramopt)

    def createTarget(self, paramopt):
        logger = getLogger()
        if paramopt is None or "store" not in paramopt:
            self.targetstore = self.supportSite
            logger.debug(__file__ + " no store option")
            return
        ropt = self.confopts.getOptions()
        for storeid in paramopt["store"]:
            if str(storeid) not in ropt["store"]:
                continue

            sname = ropt["store"][str(storeid)]["name"]

            if sname not in self.supportSite:
                continue

            self.targetstore.append(sname)

    def getSiteSearch(self, name):
        return self.searchs[name]

    def getSite(self, name):
        return self.searchs[name].getSite()

    def getRequestOpt(self, name):
        return self.searchs[name].getRequestOpt()

    def getParser(self, name):
        return self.searchs[name].getParser()


def searchResult(taskq, retq, wtime: int):
    logger = getLogger()
    spr = SearchProcResult()
    try:
        searcho: SiteSearchOpt = taskq.get(timeout=wtime)
    except queue.Empty:
        logger.error(f"{__file__} taskqueue timeout")
        retq.put(spr)
        return
    site = searcho.getSite()
    if not site.isExistCategory():
        logger.info(f"{__file__} {searcho.getName()} no exist category")
        retq.put(spr)
        return
    retbool, html = downloadHtml(searcho, logger)
    if not retbool:
        logger.error(__file__ + " fail download")
        retq.put(spr)
        return
    parseHtml(searcho, logger, spr, html)
    retq.put(spr)


def downloadHtml(searcho: SiteSearchOpt, logger: logging.Logger):
    site = searcho.getSite()
    dlopt = searcho.getRequestOpt()
    url = site.createURL()
    logger.debug(f"{__file__} start DownLoad url={url}")
    retbool, html = download_html.getUrlHtml(url, dlopt)
    logger.debug(__file__ + " end DownLoad")
    return retbool, html


def parseHtml(
    searcho: SiteSearchOpt,
    logger: logging.Logger,
    spr: SearchProcResult,
    html: str,
):
    logger.debug(f"{__file__} start item parse name={searcho.name}")
    parser = searcho.getParser()
    parser.parseSearch(html)
    logger.debug(f"{__file__} end item parse name={searcho.name}")
    items = parser.getItems()
    spr.setItems(items)
    if len(items) > 0:
        logger.debug(f"{__file__} start page parse name={searcho.name}")
        spr.setPageInfo(parser.getPage())
        logger.debug(f"{__file__} end page parse name={searcho.name}")


class SearchItem:
    sopt: SearchOpt
    allitems: list[dict]
    pageinfo: dict

    def __init__(self, sword: str, optjson: dict | None = None):
        self.sopt = self.createOption(sword, optjson)

    def createOption(self, sword: str, optjson: dict | None = None):
        sopt = SearchOpt(sword)
        sopt.setParamOpt(optjson)
        return sopt

    def start(self):
        self.allitems = []
        self.pageinfo = None
        pageinfo = {SearchCmn.ENABLE: SearchCmn.FALSE}
        sopt = self.sopt
        self.setCurrentPage(pageinfo, sopt.getParamOpt())

        logger = getLogger()
        logger.debug(__file__ + " start SearchItem")
        m = Manager()
        retq = m.Queue()
        taskq = m.Queue()
        procs: list[Process] = []
        waittime = QUEUE_TIMEOUT
        for sitename in sopt.targetstore:
            searcho = sopt.getSiteSearch(sitename)
            taskq.put(searcho)
            proc = Process(target=searchResult, args=(taskq, retq, waittime))
            proc.start()
            procs.append(proc)

        for proc in procs:
            proc.join()

        for i in range(len(procs)):
            try:
                spr: SearchProcResult = retq.get(timeout=waittime)
                self.allitems.extend(spr.getItems())
                self.setPage(pageinfo, spr.getPageInfo())
                self.pageinfo = pageinfo
            except queue.Empty:
                logger.error("{}  [{}] retqueue timeout".format(__file__, str(i)))
        logger.debug(f"{__file__} allitems={self.allitems}")
        logger.debug(f"{__file__} pageinfo={self.pageinfo}")
        if SearchCmn.TRUE != pageinfo[SearchCmn.ENABLE]:
            logger.debug(__file__ + " end SearchItem")
            return

        logger.debug(__file__ + " end SearchItem")

    def setCurrentPage(self, pageinfo, urlparam):
        if SearchCmn.PAGE not in urlparam:
            pageinfo[SearchCmn.CURRENT] = "1"
            return
        pageinfo[SearchCmn.CURRENT] = urlparam[SearchCmn.PAGE]

    def setPage(self, pageinfo, searchret):
        if searchret is None:
            return
        if SearchCmn.ENABLE not in searchret:
            return
        if SearchCmn.TRUE != searchret[SearchCmn.ENABLE]:
            return

        pageinfo[SearchCmn.ENABLE] = SearchCmn.TRUE
        MAX = SearchCmn.MAX
        MIN = SearchCmn.MIN

        if MAX not in pageinfo:
            pageinfo[MAX] = int(searchret[MAX])
        elif int(pageinfo[MAX]) < int(searchret[MAX]):
            pageinfo[MAX] = int(searchret[MAX])

        if MIN not in pageinfo:
            pageinfo[MIN] = int(searchret[MIN])
        elif int(pageinfo[MIN]) > int(searchret[MIN]):
            pageinfo[MIN] = int(searchret[MIN])

        if SearchCmn.MOREPAGE in searchret:
            pageinfo[SearchCmn.MOREPAGE] = SearchCmn.TRUE

    def getPageInfo(self):
        return self.pageinfo

    def getItems(self):
        return self.allitems

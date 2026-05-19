import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field

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

QUEUE_TIMEOUT = 10


def getLogger():
    logname = cmnlog.LogName.SEARCH
    return cmnlog.getLogger(logname)


class SearchCacheManager:
    def __init__(self):
        self.enabled = getcache.isSearchCacheFunc()

    def _generate_key(self, sword: str, optjson: dict | None) -> str:
        key = sword
        if optjson is not None:
            jsontext = json.dumps(optjson)
            key += " " + jsontext
        return key

    def get(self, sword: str, optjson: dict | None) -> str:
        if self.enabled:
            key = self._generate_key(sword, optjson)
            return getcache.getSearchCache().read(key)
        return ""

    def set(self, sword: str, optjson: dict | None, text: str):
        if self.enabled:
            key = self._generate_key(sword, optjson)
            getcache.getSearchCache().write(key, text)


class SearchService:
    def __init__(self):
        self.cache_manager = SearchCacheManager()

    def perform_search(self, sword: str, optjson: dict | None = None) -> dict:
        # キャッシュの確認
        cache_data = self.cache_manager.get(sword, optjson)
        if cache_data:
            return json.loads(cache_data)

        # 検索の実行
        orchestrator = SearchOrchestrator(sword, optjson)
        orchestrator.execute_searches()

        # 結果の構築
        res = {
            SearchParser.ITEMS: orchestrator.getItems(),
            SearchParser.PAGE: orchestrator.getPageInfo(),
        }

        # キャッシュへの保存
        self.cache_manager.set(sword, optjson, json.dumps(res))
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
    service = SearchService()
    res = service.perform_search(sword, optdict)
    logger.debug(__file__ + " end Search")
    logger.info(__file__ + " end url_search")
    return {RESULT_KEY: res}


@dataclass
class SiteSearchResult:
    site_name: str
    items: list[dict] = field(default_factory=list)
    page_info: dict = field(default_factory=dict)
    error: str | None = None


class SearchOpt:
    SURUGAYA = "surugaya"
    BOOKOFF = "bookoff"
    NETOFF = "netoff"

    # サポートするサイト名と、対応するオプションクラスの定義
    _SITE_MAP = {
        SURUGAYA: surugayaSearchOpt.SurugayaSearchOpt,
        NETOFF: netoffSearchOpt.NetoffSearchOpt,
        BOOKOFF: bookoffSearchOpt.BookoffSearchOpt,
    }

    def __init__(self, word):
        self.confopts = readoption.ReadSearchOpt()
        self.searchs: dict[str, SiteSearchOpt] = self._init_search_options()
        self.urlparam = {FilterQueryName.WORD.value: word}
        self.targetstore: list[str] = []
        self.supportSite = list(self._SITE_MAP.keys())

        self.setWord(word)

    def _init_search_options(self) -> dict[str, SiteSearchOpt]:
        """登録されている全てのサイト検索オプションを動的に初期化する"""
        return {
            name: opt_class(self.confopts) for name, opt_class in self._SITE_MAP.items()
        }

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


def searchResult(searcho: SiteSearchOpt) -> SiteSearchResult:
    logger = getLogger()
    result = SiteSearchResult(site_name=searcho.getName())
    try:
        site = searcho.getSite()
        if not site.isExistCategory():
            logger.info(f"{__file__} {searcho.getName()} no exist category")
            return result

        retbool, html = downloadHtml(searcho, logger)
        if not retbool:
            logger.error(f"{__file__} {searcho.getName()} fail download")
            result.error = "fail download"
            return result

        parseHtml(searcho, logger, result, html)
    except Exception as e:
        logger.exception(f"Error searching {searcho.getName()}: {e}")
        result.error = str(e)
    return result


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
    result: SiteSearchResult,
    html: str,
):
    logger.debug(f"{__file__} start item parse name={searcho.getName()}")
    parser = searcho.getParser()
    parser.parseSearch(html)
    logger.debug(f"{__file__} end item parse name={searcho.getName()}")
    items = parser.getItems()
    result.items = items
    if len(items) > 0:
        logger.debug(f"{__file__} start page parse name={searcho.getName()}")
        result.page_info = parser.getPage()
        logger.debug(f"{__file__} end page parse name={searcho.getName()}")


class SearchOrchestrator:
    sopt: SearchOpt
    allitems: list[dict]
    pageinfo: dict | None

    def __init__(self, sword: str, optjson: dict | None = None):
        self.sopt = self.createOption(sword, optjson)
        self.allitems = []
        self.pageinfo = None

    def createOption(self, sword: str, optjson: dict | None = None):
        sopt = SearchOpt(sword)
        sopt.setParamOpt(optjson)
        return sopt

    def execute_searches(self):
        pageinfo = {SearchCmn.ENABLE: SearchCmn.FALSE}
        self.setCurrentPage(pageinfo, self.sopt.getParamOpt())

        logger = getLogger()
        logger.debug(f"{__file__} start SearchOrchestrator")

        with ProcessPoolExecutor() as executor:
            future_to_site = {
                executor.submit(searchResult, self.sopt.getSiteSearch(name)): name
                for name in self.sopt.targetstore
            }

            for future in as_completed(future_to_site, timeout=QUEUE_TIMEOUT):
                site_name = future_to_site[future]
                try:
                    result: SiteSearchResult = future.result()
                    if result.error:
                        logger.error(f"Search error in {site_name}: {result.error}")

                    self.allitems.extend(result.items)
                    self.setPage(pageinfo, result.page_info)
                except Exception as exc:
                    logger.error(f"{site_name} generated an exception: {exc}")

        self.pageinfo = pageinfo
        logger.debug(f"{__file__} allitems count={len(self.allitems)}")
        logger.debug(f"{__file__} end SearchOrchestrator")

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

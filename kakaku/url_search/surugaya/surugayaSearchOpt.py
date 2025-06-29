import os
from datetime import datetime, timezone, timedelta

from url_search import siteSearchOpt
from url_search import readoption
from url_search.surugaya import surugayaURL
from downloader import requestoption
from html_parser import surugaya_search

from common import read_config
from common.filter_name import FilterQueryName


class SurugayaSearchOpt(siteSearchOpt.SiteSearchOpt):
    COOKIE_FNAME = "surugaya_cookie.lwp"
    fixed_cookies = [
        {
            "name": "safe_search_expired",
            "value": "1",
        },
        {"name": "safe_search_option", "value": "3"},
    ]

    def __init__(self, confopt: readoption.ReadSearchOpt):
        self.name = "surugaya"
        self.confopt = confopt
        self.site = surugayaURL.SurugayaURL(confopt)
        self.requestOpt = requestoption.RequestOpt(name=self.name)
        is_surugaya_url_convert = read_config.get_surugaya_search_result_url_convert()
        self.parser = surugaya_search.SearchSurugaya(
            is_converturl=is_surugaya_url_convert or False
        )

    def setSearchWord(self, word: str):
        self.site.setWord(word)

    def setParamOpt(self, paramopt):
        self.site.setParameter(paramopt)
        self.setSafeSearchParam(paramopt)

    def create_fixed_cookies(self):
        now = datetime.now(timezone.utc)
        oyl = now + timedelta(days=365)
        results = []
        for cookie in self.fixed_cookies:
            d = {
                "domain": "www.suruga-ya.jp",
                "path": "/",
                "version": "0",
                "expires": oyl.timestamp(),
            } | cookie
            results.append(d)
        return results

    def setSafeSearchParam(self, paramopt):
        if FilterQueryName.SAFES.value not in paramopt:
            return

        num = -1
        try:
            num = int(paramopt[FilterQueryName.SAFES.value])
        except:
            pass
        if num == 0:
            opt: requestoption.RequestOpt = self.requestOpt
            opt.set_cookie_dir(
                os.path.join(read_config.get_search_option_path(), "surugaya")
            )
            opt.set_cookie_filename(SurugayaSearchOpt.COOKIE_FNAME)
            opt.set_fixed_cookies_dict(self.create_fixed_cookies())

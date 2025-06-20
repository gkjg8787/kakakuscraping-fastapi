import os
from datetime import datetime, timezone, timedelta

from url_search import siteSearchOpt
from url_search.netoff import netoffURL
from downloader import requestoption
from html_parser import netoff_search

from common import read_config
from common.filter_name import FilterQueryName


class NetoffSearchOpt(siteSearchOpt.SiteSearchOpt):
    COOKIE_FNAME = "netoff_cookie.lwp"
    fixed_cookies = [
        {
            "name": "r18flg",
            "value": "1",
        },
    ]

    def __init__(self, confopt):
        self.name = "netoff"
        self.confopt = confopt
        self.site = netoffURL.NetoffURL(confopt)
        self.requestOpt = requestoption.RequestOpt(
            name=self.name,
            is_visit_cookies=True,
            cookie_dir=os.path.join(read_config.get_search_option_path(), "netoff"),
            cookie_filename=NetoffSearchOpt.COOKIE_FNAME,
        )
        self.parser = netoff_search.SearchNetoff()

    def setSearchWord(self, word):
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
                "domain": "www.netoff.co.jp",
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
            self.requestOpt.set_fixed_cookies_dict(self.create_fixed_cookies())

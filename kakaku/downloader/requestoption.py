from http.cookiejar import LWPCookieJar, LoadError
import datetime
from dataclasses import dataclass
import os
import json

import requests

from common import cmnlog


class UserAgent:
    value = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    def to_dict(self) -> dict:
        return {"User-Agent": self.value}


class HttpClientHints:
    sec_ch_ua: str = '"Not)A;Brand";v="99","Google Chrome";v="127","Chromium";v="127"'
    sec_ch_ua_mobile: str = "?0"
    sec_ch_ua_platform: str = '"Windows"'
    sec_fetch_mode: str = "navigate"
    sec_fetch_dest: str = "document"
    sec_fetch_site: str = "none"
    sec_fetch_user: str = "?1"

    def to_dict(self) -> dict:
        result = {
            "Sec-Ch-Ua": self.sec_ch_ua,
            "Sec-Ch-Ua-Moblie": self.sec_ch_ua_mobile,
            "Sec-Ch-Ua-Platform": self.sec_ch_ua_platform,
            "Sec-Fetch-Mode": self.sec_fetch_mode,
            "Sec-Fetch-Dest": self.sec_fetch_dest,
            "Sec-Fetch-Site": self.sec_fetch_site,
            "Sec-Fetch-User": self.sec_fetch_user,
        }
        return result


@dataclass
class RequestOpt:
    userAgent: bool = True
    selenium: bool = False
    jsWaitTime: int = 3
    cookiejar: LWPCookieJar | None = None
    is_visit_cookies: bool = False
    cookie_dir: str = ""
    name: str = ""
    cookie_filename: str = ""
    fixed_cookies: list[dict] | None = None

    def isUserAgent(self):
        return self.userAgent

    def isCookieJar(self):
        if not self.get_cookie_filepath():
            return False
        # if self.cookiejar is None : return False
        return True

    def load_cookie(self):
        fpath = self.get_cookie_filepath()
        if not os.path.exists(fpath):
            return None
        loaded_cookie_dict = json.load(fpath)
        return requests.utils.cookiejar_from_dict(loaded_cookie_dict)

    def add_fixed_cookie(self, cookies: requests.cookies.RequestsCookieJar):
        if not self.fixed_cookies:
            return cookies
        for add_cookie in self.fixed_cookies:
            cookies.set(
                add_cookie["name"],
                add_cookie["value"],
                domain=add_cookie["domain"],
                path=add_cookie["path"],
                expires=add_cookie["expires"],
                version=add_cookie["version"],
            )
        return cookies

    def getCookieJar(self):
        if self.isCookieJar() and self.cookiejar is None:
            cookiejar = self.load_cookie()
            if cookiejar is None:
                cookiejar = requests.cookies.RequestsCookieJar()
            cookiejar = self.add_fixed_cookie(cookiejar)
        return self.cookiejar

    def getHeader(self):
        if not self.userAgent:
            return None
        header = UserAgent().to_dict()
        header.update(HttpClientHints().to_dict())
        return header

    def updateCookieJar(self, cookiejar: LWPCookieJar):
        nd = datetime.datetime.now(datetime.timezone.utc)
        oyl = nd + datetime.timedelta(days=365)
        isUpdate = False
        for c in cookiejar:
            if int(c.expires) < nd.timestamp():
                c.__dict__["expires"] = oyl.timestamp()
                isUpdate = True
        if isUpdate:
            cookiejar.save()

    def get_cookie_filepath(self):
        return os.path.join(self.cookie_dir, self.cookie_filename)

    def needs_visit_cookies(self):
        return self.is_visit_cookies

    def set_cookie(self, cookies: any, save: bool = True):
        self.cookiejar = cookies
        if save:
            fpath = self.get_cookie_filepath()
            with open(fpath, "w") as f:
                json.dump(cookies.get_dict(), f)

    def set_cookie_dir(self, dir_path: str):
        self.cookie_dir = dir_path

    def set_cookie_filename(self, filename: str):
        self.cookie_filename = filename

    def set_fixed_cookies_dict(self, cookies_dict_list: list[dict]):
        self.fixed_cookies = cookies_dict_list

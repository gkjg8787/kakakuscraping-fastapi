from http.cookiejar import LWPCookieJar, LoadError
import datetime
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


class RequestOpt:

    def __init__(self):
        self.userAgent = True
        self.selenium = False
        self.jsWaitTime = 3
        self.cookiejar = None
        self.cookiefpath = None

    def isUserAgent(self):
        return self.userAgent

    def setUserAgent(self, isSet):
        self.userAgent = isSet

    def setSelenium(self, bool):
        self.selenium = bool

    def isSelenium(self):
        return self.selenium

    def setCookieFilePath(self, fpath):
        self.cookiefpath = fpath

    def isCookieJar(self):
        if self.cookiefpath is None:
            return False
        # if self.cookiejar is None : return False
        return True

    def loadCookie(self):
        cj = LWPCookieJar(self.cookiefpath)
        try:
            cj.load(ignore_expires=True)
            self.updateCookieJar(cj)
            self.cookiejar = cj
        except LoadError:
            logger = cmnlog.getLogger(cmnlog.LogName.SEARCH)
            logger.error(__file__ + " File Cookie LoadError " + self.cookiefpath)
        except OSError:
            logger = cmnlog.getLogger(cmnlog.LogName.SEARCH)
            logger.error(__file__ + " File Cookie OSError " + self.cookiefpath)

    def getCookieJar(self):
        if self.isCookieJar() and self.cookiejar is None:
            self.loadCookie()
        return self.cookiejar

    def getJsWaitTime(self):
        return self.jsWaitTime

    def getHeader(self):
        if not self.userAgent:
            return None
        header = UserAgent().to_dict()
        header.update(HttpClientHints().to_dict())
        return header

    def updateCookieJar(self, cookiejar):
        nd = datetime.datetime.now(datetime.timezone.utc)
        oyl = nd + datetime.timedelta(days=365)
        isUpdate = False
        for c in cookiejar:
            if int(c.expires) < nd.timestamp():
                c.__dict__["expires"] = oyl.timestamp()
                isUpdate = True
        if isUpdate:
            cookiejar.save()

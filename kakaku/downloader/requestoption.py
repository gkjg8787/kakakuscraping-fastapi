from http.cookiejar import LWPCookieJar
import datetime
from common import cmnlog

class RequestOpt:
    __userAgentText = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53'
    __header = {
        'User-Agent':__userAgentText
    }
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
        if self.cookiefpath is None: return False
        #if self.cookiejar is None : return False
        return True
    
    def loadCookie(self):
        cj = LWPCookieJar(self.cookiefpath)
        try:
            cj.load(ignore_expires=True)
            self.updateCookieJar(cj)
            self.cookiejar = cj
        except:
            #cmnlog.createLogger(cmnlog.LogName.SEARCH)
            logger = cmnlog.getLogger(cmnlog.LogName.SEARCH)
            logger.error(__file__ + ' File Cookie Load '+ self.cookiefpath)
    
    def getCookieJar(self):
        if self.isCookieJar() and self.cookiejar is None:
            self.loadCookie()
        return self.cookiejar

    def getJsWaitTime(self):
        return self.jsWaitTime

    def getHeader(self):
        if not self.userAgent: return None
        return RequestOpt.__header

    def updateCookieJar(self, cookiejar):
        nd = datetime.datetime.utcnow()
        oyl = nd + datetime.timedelta(days=365)
        isUpdate = False
        for c in cookiejar:
            if int(c.expires) < nd.timestamp():
                c.__dict__['expires'] = oyl.timestamp()
                isUpdate = True
        if isUpdate:
            cookiejar.save()


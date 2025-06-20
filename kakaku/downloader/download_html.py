import os
import datetime
import hashlib

from common import read_config
from downloader.requestoption import RequestOpt
from downloader import justbeforeconfig
import requests
from requests.exceptions import Timeout

dirpath = read_config.get_dl_temp_dir()
REQUESTS_TIMEOUT = (3.5, 9.0)


def downLoadHtml(url):
    retbool, text = __getUrlHtml(url)
    if not retbool:
        return ""
    dt_now = datetime.datetime.now()
    title = url + ":" + "{0:%Y%m%d_%H%M%S_%f}".format(dt_now)
    filename = hashlib.md5(title.encode("utf-8")).hexdigest()
    with open(os.path.join(dirpath, filename), "x", encoding="UTF-8") as f:
        f.write(text)
    return dirpath + filename


def getUrlHtml(url, opt=None):
    if opt is None:
        return __getUrlHtml(url)
    else:
        return __getUrlHtml(url, opt)


def __getUrlHtml(url, opt=RequestOpt()):
    isverify = justbeforeconfig.isVerifyURL(url)
    if opt.needs_visit_cookies() and opt.cookiejar is None:
        try:
            res = requests.get(
                url=url,
                headers=opt.getHeader(),
                verify=isverify,
                timeout=REQUESTS_TIMEOUT,
            )
        except Timeout:
            return False, "Visit Timeout Error"
        opt.set_cookie(cookies=res.cookies, save=True)

    try:
        res = requests.get(
            url=url,
            headers=opt.getHeader(),
            cookies=opt.getCookieJar(),
            verify=isverify,
            timeout=REQUESTS_TIMEOUT,
        )
    except Timeout:
        return False, "Timeout Error"
    except Exception as e:
        return False, "requests Error {}".format(e)
    if res.status_code != requests.codes.ok:
        return False, "Error Status Code " + str(res.status_code)
    if opt.needs_visit_cookies():
        opt.set_cookie(cookies=res.cookies, save=True)
    # res.encoding = res.apparent_encoding
    if res.encoding.upper() == "windows-31j".upper():
        res.encoding = "SHIFT_JIS"
    elif res.encoding.upper() == "ISO-8859-1".upper():
        res.encoding = res.apparent_encoding
    return True, res.text

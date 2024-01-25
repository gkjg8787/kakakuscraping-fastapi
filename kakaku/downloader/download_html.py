import time
import datetime
import sys
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
    of = open(dirpath + filename, "x", encoding="UTF-8")
    of.write(text)
    of.close()
    return dirpath + filename


def getUrlHtml(url, opt=None):
    if opt is None:
        return __getUrlHtml(url)
    else:
        return __getUrlHtml(url, opt)


def __getUrlHtml(url, opt=RequestOpt()):
    isverify = justbeforeconfig.isVerifyURL(url)
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

    # res.encoding = res.apparent_encoding
    if res.encoding.upper() == "windows-31j".upper():
        res.encoding = "SHIFT_JIS"
    elif res.encoding.upper() == "ISO-8859-1".upper():
        res.encoding = res.apparent_encoding
    return True, res.text


if __name__ == "__main__":
    arglen = len(sys.argv)
    if arglen < 2:
        print("ERROR PARAMETER")
        sys.exit()
    time.sleep(1)
    filepath = downLoadHtml(sys.argv[1])
    print(filepath)

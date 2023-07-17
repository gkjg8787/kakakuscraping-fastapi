from urllib.parse import urlparse

from common import read_config

def getNoVerifyList():
    confstr = read_config.get_no_verify_domain()
    if len(confstr) == 0:
        return ''
    confstr = confstr.replace(',', '')
    conflist = confstr.split()
    return conflist

def isVerifyURL(url):
    parsed_url = urlparse(url)
    conflist = getNoVerifyList()
    for nvurl in conflist:
        if nvurl == parsed_url.netloc:
            return False
    
    return True
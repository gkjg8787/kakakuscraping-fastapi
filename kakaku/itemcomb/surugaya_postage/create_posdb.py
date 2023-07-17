import os
import json
from pathlib import Path
import datetime

import requests

from itemcomb.surugaya_postage.parse_makepure import SurugayaMakepure

from itemcomb.surugaya_postage.const_value import (
    userAgent,
    header,
    SHOPLIST_URL,
    SHOPLIST_FNAME,
)


def downLoadHtml(url):
    res = requests.get(url=url, headers=header, cookies=None)
    if res.status_code != requests.codes.ok :
        print('Error Status Code ' + str(res.status_code))
        return
    res.encoding = res.apparent_encoding
    charset = res.encoding
    #print('charset='+charset)

    text = res.text
    return text

def getMakepureHtml():
    return downLoadHtml(SHOPLIST_URL)

def getShopListFilePath():
    p = Path(__file__)
    return os.path.join(p.parent, SHOPLIST_FNAME)

def createShopListFile():
    text = getMakepureHtml()
    sm = SurugayaMakepure()
    sm.parse(text)
    dic = sm.getShopList()
    f = open(getShopListFilePath(),'w')
    f.write(json.dumps(dic,ensure_ascii=False))
    f.close()

def expireShopListFile():
    ftime = datetime.datetime.fromtimestamp(os.stat(getShopListFilePath()).st_mtime)
    elapsed_time = datetime.datetime.now() - ftime
    if elapsed_time.days > 0:
        return True
    else:
        return False

def grepShopList(name):
    slist = readShopList()
    res = []
    for shop in slist:
        if name in shop['shop_name']:
            res.append(shop)
    return res

def readShopList():
    f = open(getShopListFilePath(), 'r')
    jsontext = f.read()
    f.close()
    return json.loads(jsontext)

def getShopID(name):
    shoplist = readShopList()
    for shop in shoplist:
        if name == shop['shop_name']:
            return shop['shop_id']
    return -1

if __name__ == '__main__':
    createShopListFile()


import sys
import argparse
import json
import os
from pathlib import Path
import time

from typing import List

from itemcomb.surugaya_postage import create_posdb
from itemcomb.surugaya_postage import post_surugaya_postage

POST_WAIT_TIME = 0.5

def outputResult(rdict, outputtype):
    if outputtype == 'json':
        print(json.dumps(rdict, ensure_ascii=False))
        return
    for shoppos in rdict['result']:
        print(f"-------{shoppos['shop_name']}:{shoppos['shop_id']}-------")
        print(f"{shoppos}")
        print(f"---------------------------------")

def getPostage(pdict):
    #print(pdict)
    if not pdict['exact']:
        gsl = create_posdb.grepShopList(pdict['storename'])
    else:
        shopid = create_posdb.getShopID(pdict['storename'])
        gsl = [{'shop_name': pdict['storename'], 'shop_id':shopid}]
    reslist = []
    for shop in gsl:
        resdic = {}
        jdicts = post_surugaya_postage.getPrefecturePostage(shop['shop_id'], pdict['pref'])
        resdic.update(shop)
        resdic['postage'] = jdicts
        reslist.append(resdic)
        time.sleep(POST_WAIT_TIME)
    return {'result':reslist }

def checkUpdateShopList(forced_shop_update, without_shop_update):
    if not os.path.isfile(create_posdb.getShopListFilePath()):
        create_posdb.createShopListFile()
        return
    if without_shop_update:
        return
    if forced_shop_update or create_posdb.expireShopListFile():
        create_posdb.createShopListFile()
        return

def getPrefList():
    p = Path(__file__)
    dirp = 'surugaya_postage'
    pref_file_name = 'pref_name.txt'
    f = open(os.path.join(p.parent, dirp, pref_file_name))
    pl = f.read().splitlines()
    f.close()
    return pl

def inPrefList(prefs):
    pl = getPrefList()
    for p in prefs:
        if not p in pl:
            return False
    return True

def parseParamOpt(param):
    parser = argparse.ArgumentParser(description='get Shipping fee for Surugaya Marketplace')
    parser.add_argument('storename', metavar='name',help='store name', type=str)
    parser.add_argument('-x', '--exact', help='exact match', action='store_true')
    shopupdate = parser.add_mutually_exclusive_group()
    shopupdate.add_argument('-su', '--shop-update', dest='forced_shop_update',help='forced shoplist update', action='store_true', default=False)
    shopupdate.add_argument('-nsu', '--no-shop-update', dest='without_shop_update', help='without shoplist update', action='store_true', default=False)
    parser.add_argument('-ot', '--outputtype', metavar='type',help='Set output format'
                        ,choices=['text','json'], default='json', type=str)
    parser.add_argument('-p', '--pref', metavar='prefucture', help='prefecture to it is sent'
                        ,default=['東京都'], type=str, nargs='*')

    args = parser.parse_args(param)
    #print(args)
    res = { 'storename': ''}
    if not args.storename is None and len(args.storename) > 0:
        res['storename'] = args.storename
    else:
        print('parameter ng')
        sys.exit(1)

    res['exact'] = args.exact
    res['forced_shop_update'] = args.forced_shop_update
    res['without_shop_update'] = args.without_shop_update
    res['outputtype'] = args.outputtype

    if not args.pref is None and len(args.pref) > 0:
        if inPrefList(args.pref):
            res['pref'] = args.pref
        else:
            print('pref parameter ng')
            sys.exit(1)
    
    return res

def funcstart(storename :str,
              exact :bool,
              forced_shop_update :bool = False,
              without_shop_update :bool = False,
              outtype :str = "dict",
              prefectures :List[str] = ["東京都"]):
    checkUpdateShopList(forced_shop_update, without_shop_update)
    rdict = getPostage({
        'storename':storename,
        'exact':exact,
        'pref':prefectures,
    })
    if outtype == "dict":
        return rdict
    else:
        return json.dumps(rdict, ensure_ascii=False)

def cmdstart(argv):
    pdict = parseParamOpt(argv[1:])
    #print(pdict)
    checkUpdateShopList(pdict['forced_shop_update'], pdict['without_shop_update'])
    rdict = getPostage(pdict)
    outputResult(rdict, pdict['outputtype'])

if __name__ == '__main__':
    cmdstart(sys.argv)
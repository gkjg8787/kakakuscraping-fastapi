import sys
import argparse
import json


from itemcomb import sumitemcomb, storepostage

from accessor.item import (
    ItemQuery,
)
from accessor.store import StoreQuery

def getBoundaryInDict(d):
    BOUNDARY = 'boundary'
    if not BOUNDARY in d or d[BOUNDARY] is None:
        return '0<='
    return d[BOUNDARY]

def getPostageInDict(d):
    POSTAGE = 'postage'
    if not POSTAGE in d or d[POSTAGE] is None:
        return '0'
    return d[POSTAGE]

def createStoreConf(itemidlist):
    res = ItemQuery.get_current_storename_list_by_item_id(itemidlist)
    if res is None or len(res) == 0:
        return {}
    storenames = [t for r in res for t in r]
    sp = StoreQuery.get_storepostage_by_storename(storenames)
    dicl = [dict(row._mapping.items()) for row in sp]
    storeconf = {}
    for d in dicl:
        if not d['storename'] in storeconf:
            storeconf[d['storename']] = list()
        vald = {}
        vald['boundary'] = getBoundaryInDict(d)
        vald['postage'] = getPostageInDict(d)
        storeconf[d['storename']].append(vald)
    return storeconf

def startCalcSumitemComb(itemidlist):
    res = ItemQuery.get_latest_price_by_item_id_list(itemidlist)
    itemlist = [dict(row._mapping.items()) for row in res]
    #print(itemlist)
    storeconf = createStoreConf(itemidlist)
    #print(storeconf)
    ret = sumitemcomb.searchcomb(storeconf, itemlist, 'json')
    return ret

def getCalcSumitemComb():
    cmdstr, itemidlist, updateterms = parseParamOpt()
    if cmdstr == 'idcalc':
        ret = startCalcSumitemComb(itemidlist)
        return ret
    elif cmdstr == 'upcalc':
        storepostage.updateShippingTerms(updateterms)
        ret = startCalcSumitemComb(itemidlist)
        return ret

def startcmd():
    res = getCalcSumitemComb()
    #htmltext = sumitemcomb_adapt_deco.createHtml(json.loads(res))
    #print(htmltext)
    return res

def parseParamOpt():
    parser = argparse.ArgumentParser(description='get iteminfo and passing to sumitemcomb.py')
    parser.add_argument('-i', '--itemid', metavar='id',help='List of selected items', type=int, nargs='+')
    parser.add_argument('-s', '--store', metavar='json',help='store shipping information in json format')
    args = parser.parse_args()
    #print(args)
    if args.itemid is None:
        #print('--itemid are required')
        sys.exit(1)
    if not args.store is None and len(args.store) > 0:
        updateterms = json.loads(str(args.store))
        return 'upcalc',args.itemid, updateterms

    return 'idcalc',args.itemid, ''


if __name__ == '__main__':
    startcmd()
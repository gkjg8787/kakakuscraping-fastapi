
from typing import List
import argparse
import json
import datetime


from model.store import Store, StorePostage
from accessor.store import StoreQuery
from accessor.item import ItemQuery
from itemcomb import itemcomb_error

class StoreDictKey:
    STORE = "store"
    STORES = "stores"
    STORENAME = "storename"
    STORE_ID = "store_id"
    STOREPOSTAGE = "storepostage"
    TERMS_ID = "terms_id"
    BOUNDARY = "boundary"
    POSTAGE = "postage"

class FuncType:
    ITEM_ID = "item_id"
    STORENAME = "storename"
    UPDATE_TERMS = "updateterms"

class StorePostageResultName:
    RESULT = "result"
    ERROR = "error"

def jsonToStoreModel(jsondict):
    res = []
    for store in jsondict[StoreDictKey.STORES]:
        storeres = {}
        st = Store(
            storename=store[StoreDictKey.STORENAME]
            ,store_id=store[StoreDictKey.STORE_ID]
        )
        storeres[StoreDictKey.STORE] = st

        res_pos = []
        for pos in store[StoreDictKey.STOREPOSTAGE]:
            sp = StorePostage(
                store_id=pos[StoreDictKey.STORE_ID]
                ,terms_id=pos[StoreDictKey.TERMS_ID]
                ,boundary=pos[StoreDictKey.BOUNDARY]
                ,postage=pos[StoreDictKey.POSTAGE]
            )
            res_pos.append(sp)
        storeres[StoreDictKey.POSTAGE] = res_pos

        res.append(storeres)
    return res


def updateShippingTerms(shippingterms):
    storeinfo = jsonToStoreModel(shippingterms)
    storeidlist = [sp[StoreDictKey.STORE].store_id for sp in storeinfo]
    StoreQuery.delete_storepostage_by_store_id_list(storeidlist)
    storepostages = [sp for sps in storeinfo for sp in sps[StoreDictKey.POSTAGE]]
    StoreQuery.insert_storepostage_list(storepostages)

def update_shippingterms(store_id_list :List[int], storepostage_list :List):
    StoreQuery.delete_storepostage_by_store_id_list(store_id_list)
    StoreQuery.insert_storepostage_list(storepostage_list)

def getAndRegistShippingTerms(storenames):
    StoreQuery.regist_stores(storenames)
    res = StoreQuery.get_storepostage_by_storename(storenames)
    dicl = []
    for row in res:
        dic = {}
        for k,v in row._mapping.items():
            dic[k] = v
        dicl.append(dic)
    resdic = {}
    resdic[StorePostageResultName.RESULT] = dicl
    return resdic

def getAndRegistShippingTermsByItemId(itemids :List[int]):
    res = ItemQuery.get_current_storename_list_by_item_id(itemids)
    if res is None or len(res) == 0:
        return {StorePostageResultName.ERROR:itemcomb_error.NO_STORE_DATA}
    storenames = [t for r in res for t in r]
    return getAndRegistShippingTerms(storenames)

def parseParamOpt():
    parser = argparse.ArgumentParser(description='ctrl Shipping Terms')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-sn', '--storename', metavar='name',help='List of store name', type=str, nargs='+')
    group.add_argument('-ut', '--updateterms', metavar='json',help='store shipping information in json format')
    group.add_argument('-i', '--itemid', metavar='id',help='List of item id', type=int, nargs='+')
    
    parser.add_argument('-ot', '--outputtype', metavar='type',help='Set output format at storename or itemid'
                        ,choices=['tag','json'], default='json', type=str)

    args = parser.parse_args()
    #print(args)
    if not args.itemid is None and len(args.itemid) > 0:
        return FuncType.ITEM_ID, args.itemid, args.outputtype
    if not args.updateterms is None and len(args.updateterms) > 0:
        updateterms = json.loads(str(args.updateterms))
        return FuncType.UPDATE_TERMS, updateterms, args.outputtype
    if not args.storename is None and len(args.storename) > 0:
        return FuncType.STORENAME, args.storename, args.outputtype
    print('parameter ng')
    return '', (), args.outputtype

def json_serial(obj):
    if isinstance(obj, (datetime.datetime)):
        return obj.isoformat()
    # 上記以外はサポート対象外.
    raise TypeError ("Type %s not serializable" % type(obj))

def resultTotype(res, typestr, itemids=[]):
    if typestr == 'json':
        return json.dumps(res, default=json_serial)
    
    #text =  storepostage_deco.createHtml(res, itemids)
    #return text
    return res


def startcmd():
    cmdtype, res, outtype = parseParamOpt()
    if cmdtype == FuncType.ITEM_ID:
        result = getAndRegistShippingTermsByItemId(res)
        res = resultTotype(result, outtype, res)
        print(res)
        return
    if cmdtype == FuncType.STORENAME:
        result = getAndRegistShippingTerms(res)
        res = resultTotype(result, outtype)
        print(res)
        return
    if cmdtype == FuncType.UPDATE_TERMS:
        updateShippingTerms(res)
        return

if __name__ == '__main__':
    startcmd()
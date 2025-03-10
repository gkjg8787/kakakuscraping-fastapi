import argparse
import json
import datetime

from sqlalchemy.orm import Session

from model.store import Store, StorePostage
from accessor.read_sqlalchemy import get_session
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
    res: list[dict[str, Store]] = []
    for store in jsondict[StoreDictKey.STORES]:
        storeres: dict[str, Store] = {}
        st = Store(
            storename=store[StoreDictKey.STORENAME],
            store_id=store[StoreDictKey.STORE_ID],
        )
        storeres[StoreDictKey.STORE] = st

        res_pos: list[StorePostage] = []
        for pos in store[StoreDictKey.STOREPOSTAGE]:
            sp = StorePostage(
                store_id=pos[StoreDictKey.STORE_ID],
                terms_id=pos[StoreDictKey.TERMS_ID],
                boundary=pos[StoreDictKey.BOUNDARY],
                postage=pos[StoreDictKey.POSTAGE],
            )
            res_pos.append(sp)
        storeres[StoreDictKey.POSTAGE] = res_pos

        res.append(storeres)
    return res


def updateShippingTerms(db: Session, shippingterms: dict):
    storeinfo = jsonToStoreModel(shippingterms)
    storeidlist = [sp[StoreDictKey.STORE].store_id for sp in storeinfo]
    StoreQuery.delete_storepostage_by_store_id_list(db, store_id_list=storeidlist)
    storepostages = [sp for sps in storeinfo for sp in sps[StoreDictKey.POSTAGE]]
    StoreQuery.insert_storepostage_list(db, storepostage_list=storepostages)


def update_shippingterms(
    db: Session, store_id_list: list[int], storepostage_list: list
):
    StoreQuery.delete_storepostage_by_store_id_list(db, store_id_list=store_id_list)
    StoreQuery.insert_storepostage_list(db, storepostage_list=storepostage_list)


def getAndRegistShippingTerms(db: Session, storenames: list[str], fq: dict = {}):
    StoreQuery.regist_stores(db, storename_list=storenames)
    res = StoreQuery.get_storepostage_by_storename(db=db, storenames=storenames, fq=fq)
    dicl = [dict(row._mapping.items()) for row in res]
    resdic: dict[list[dict]] = {}
    resdic[StorePostageResultName.RESULT] = dicl
    return resdic


def getAndRegistShippingTermsByItemId(db: Session, itemids: list[int], fq: dict = {}):
    res = ItemQuery.get_current_storename_list_by_item_id(db, item_id_list=itemids)
    if res is None or len(res) == 0:
        count = ItemQuery.get_count_of_pricelog_2days_for_today_by_item_id(
            db, item_id_list=itemids
        )
        if not count:
            return {
                StorePostageResultName.ERROR: itemcomb_error.ItemCombError.NO_TODAY_LOG
            }
        else:
            return {
                StorePostageResultName.ERROR: itemcomb_error.ItemCombError.NO_STORE_DATA
            }

    storenames: list[str] = [t for r in res for t in r]
    return getAndRegistShippingTerms(db=db, storenames=storenames, fq=fq)


def parseParamOpt():
    parser = argparse.ArgumentParser(description="ctrl Shipping Terms")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-sn",
        "--storename",
        metavar="name",
        help="List of store name",
        type=str,
        nargs="+",
    )
    group.add_argument(
        "-ut",
        "--updateterms",
        metavar="json",
        help="store shipping information in json format",
    )
    group.add_argument(
        "-i", "--itemid", metavar="id", help="List of item id", type=int, nargs="+"
    )

    parser.add_argument(
        "-ot",
        "--outputtype",
        metavar="type",
        help="Set output format at storename or itemid",
        choices=["tag", "json"],
        default="json",
        type=str,
    )

    args = parser.parse_args()
    # print(args)
    if args.itemid is not None and len(args.itemid) > 0:
        return FuncType.ITEM_ID, args.itemid, args.outputtype
    if args.updateterms is not None and len(args.updateterms) > 0:
        updateterms = json.loads(str(args.updateterms))
        return FuncType.UPDATE_TERMS, updateterms, args.outputtype
    if args.storename is not None and len(args.storename) > 0:
        return FuncType.STORENAME, args.storename, args.outputtype
    print("parameter ng")
    return "", (), args.outputtype


def json_serial(obj):
    if isinstance(obj, (datetime.datetime)):
        return obj.isoformat()
    # 上記以外はサポート対象外.
    raise TypeError("Type %s not serializable" % type(obj))


def resultTotype(res, typestr, itemids=[]):
    if typestr == "json":
        return json.dumps(res, default=json_serial)

    # text =  storepostage_deco.createHtml(res, itemids)
    # return text
    return res


def startcmd():
    cmdtype, res, outtype = parseParamOpt()
    db = next(get_session())
    if cmdtype == FuncType.ITEM_ID:
        result = getAndRegistShippingTermsByItemId(db, res)
        res = resultTotype(result, outtype, res)
        print(res)
        return
    if cmdtype == FuncType.STORENAME:
        result = getAndRegistShippingTerms(db, res)
        res = resultTotype(result, outtype)
        print(res)
        return
    if cmdtype == FuncType.UPDATE_TERMS:
        updateShippingTerms(db, res)
        return


if __name__ == "__main__":
    startcmd()

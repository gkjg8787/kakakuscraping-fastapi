import os
import datetime
from enum import Enum, auto

from sqlalchemy.orm import Session

from accessor.item import (
    NewestQuery,
    ItemQuery,
    UrlQuery,
    UrlActive,
)
from accessor import store
from html_parser import (
    gethtmlparse,
    htmlparse,
)
from common import read_config, const_value
from common.util import isLocalToday, utcTolocaltime
from itemcomb import postage_data as posd

# from common.stop_watch import stop_watch


def deleteTempFile(fname):
    isAutoDel = read_config.is_auto_del_dl_file()
    if isAutoDel:
        os.remove(fname)


def logprint(text: str, isError: bool, logger=None):
    if logger is None:
        print(text)
        return
    elif isError:
        logger.error(__file__ + ", " + text)
        return
    else:
        logger.info(__file__ + ", " + text)
        return


def getLowestPrice(an: int, bn: int):
    if an == const_value.INIT_PRICE:
        return bn
    if bn == const_value.INIT_PRICE:
        return an
    if an < bn:
        return an
    return bn


def get_oldprice(
    db: Session, item_id: int = const_value.NONE_ID, url_id: int = const_value.NONE_ID
):
    if item_id > const_value.NONE_ID:
        oldprice = ItemQuery.get_most_recent_old_price_of_2days_by_item_id(
            db, item_id=item_id
        )
        if oldprice:
            return oldprice
        return const_value.INIT_PRICE
    if url_id > const_value.NONE_ID:
        oldprice = ItemQuery.get_most_recent_old_price_of_2days_by_url_id(
            db, url_id=url_id
        )
        if oldprice:
            return oldprice
        return const_value.INIT_PRICE
    return const_value.INIT_PRICE


def convert_newestitem(pddict) -> dict:
    ret = {
        "url_id": pddict["url_id"],
        "created_at": pddict["created_at"],
        "newestprice": getLowestPrice(pddict["usedprice"], pddict["newprice"]),
        "taxin": pddict["taxin"],
        "onsale": pddict["onsale"],
        "salename": pddict["salename"],
        "trendrate": pddict["trendrate"],
        "storename": pddict["storename"],
    }
    return ret


def convert_pricelog(pddict) -> dict:
    ret = pddict.copy()
    del ret["oldprice"]
    return ret


def update_newestitem(db: Session, pddict):
    if pddict is None:
        return
    nidict = convert_newestitem(pddict)
    NewestQuery.update_items_by_dict(db, nidict=nidict)


def update_itemsname(db: Session, url_id: int, uniqname: str):
    ItemQuery.update_items_name_by_url_id(db, url_id=url_id, uniqname=uniqname)


def update_stores(db: Session, storename_list: list[str]):
    add_storename_list = get_add_storename(db, storename_list=storename_list)
    store.StoreQuery.add_storename_list(db, storename_list=add_storename_list)


def combine_duplicates_item(parseitems: htmlparse.ParseItems):
    items = parseitems.getItems()
    if len(items) == 1:
        return items
    dup_dict: dict[str, htmlparse.ParseItemInfo] = {}

    for item in items:
        if item.storename not in dup_dict:
            dup_dict[item.storename] = item
            continue
        else:
            d = dup_dict[item.storename]
            is_combine = False
            if is_combine_price(d.newPrice, item.newPrice):
                is_combine = True
                d.newPrice = item.newPrice
            if is_combine_price(d.usedPrice, item.usedPrice):
                is_combine = True
                d.usedPrice = item.usedPrice
            if is_combine and not d.onSale and item.onSale:
                d.onSale = item.onSale
                d.saleName = item.saleName
            continue
    return [v for v in dup_dict.values()]


def is_combine_price(cur: int, insert: int):
    if cur == const_value.INIT_PRICE and insert != const_value.INIT_PRICE:
        return True
    if (
        cur != const_value.INIT_PRICE
        and insert != const_value.INIT_PRICE
        and cur > insert
    ):
        return True
    return False


def update_itemsprices(
    db: Session, parseitems: htmlparse.ParseItems, item_id: int, url_id: int
):
    if item_id and int(item_id) != const_value.NONE_ID:
        oldprice = get_oldprice(db, item_id=item_id)
    else:
        oldprice = get_oldprice(db, url_id=url_id)
    pricelog_list = ItemQuery.get_pricelog_2days_by_url_id(db, url_id=url_id)
    storename_list = []
    items = combine_duplicates_item(parseitems=parseitems)
    is_update_itemsname = False
    lowest_pricedatadict = None
    for pd in items:
        pd.oldPrice = oldprice
        pricedatadict = pd.getOrderedDict()
        if not is_update_itemsname:
            is_update_itemsname = True
            update_itemsname(
                db,
                url_id=int(pricedatadict["url_id"]),
                uniqname=pricedatadict["uniqname"],
            )
        update_itemsprice(db, pricedatadict=pricedatadict, pricelog_list=pricelog_list)
        storename_list.append(pricedatadict["storename"])
        lowest_pricedatadict = min_pricedatadict(lowest_pricedatadict, pricedatadict)
        continue
    update_newestitem(db, pddict=lowest_pricedatadict)
    update_stores(db, storename_list=storename_list)


def min_pricedatadict(p1: dict | None, p2: dict):
    if p1 is None:
        return p2
    else:
        lowestprice = getLowestPrice(p2["usedprice"], p2["newprice"])
        if lowestprice != const_value.INIT_PRICE:
            p1_lowest = getLowestPrice(p1["usedprice"], p1["newprice"])
            if p1_lowest == const_value.INIT_PRICE:
                return p2
            if lowestprice < p1_lowest:
                return p2
    return p1


def get_add_storename(db: Session, storename_list: list[str]):
    add_list = []
    db_storename_list = [s.storename for s in store.StoreQuery.get_all(db)]
    for storename in storename_list:
        if storename not in db_storename_list:
            add_list.append(storename)
    return add_list


# @stop_watch
def upsert_pricelog(db: Session, pldict: dict, newest_pricelog):
    if newest_pricelog and isLocalToday(utcTolocaltime(newest_pricelog.created_at)):
        if __is_update_price(
            insert_new=pldict["newprice"],
            insert_used=pldict["usedprice"],
            db_new=newest_pricelog.newprice,
            db_used=newest_pricelog.usedprice,
        ):
            ItemQuery.update_pricelog_2days_by_dict_and_log_id(
                db, pldict=pldict, log_id=newest_pricelog.log_id
            )
            return True
        if __is_add_price(
            insert_new=pldict["newprice"],
            insert_used=pldict["usedprice"],
            db_new=newest_pricelog.newprice,
            db_used=newest_pricelog.usedprice,
        ):
            ItemQuery.add_pricelog_2days_by_dict(db, pldict=pldict)
            return True
        return False
    else:
        ItemQuery.add_pricelog_2days_by_dict(db, pldict=pldict)
        return True


def __is_add_price(insert_new: int, insert_used: int, db_new: int, db_used: int):
    if insert_new == db_new and insert_used == db_used:
        return False
    return True


def __is_update_price(insert_new: int, insert_used: int, db_new: int, db_used: int):
    if (
        db_new == const_value.INIT_PRICE
        and insert_new != const_value.INIT_PRICE
        and insert_used == db_used
    ):
        return True
    if (
        db_used == const_value.INIT_PRICE
        and insert_used != const_value.INIT_PRICE
        and insert_new == db_new
    ):
        return True
    return False


def get_newest_pricelog(pricelog_list: list, url_id: int, storename: str):
    newest = None
    for pricelog in pricelog_list:
        if pricelog.url_id != url_id or pricelog.storename != storename:
            continue
        if newest is None:
            newest = pricelog
            continue
        elif newest.created_at < pricelog.created_at:
            newest = pricelog
        continue
    return newest


# @stop_watch
def update_itemsprice(db: Session, pricedatadict: dict, pricelog_list: list):
    newest_pricelog = get_newest_pricelog(
        pricelog_list, pricedatadict["url_id"], pricedatadict["storename"]
    )
    pldict = convert_pricelog(pricedatadict)
    upsert_pricelog(db, pldict=pldict, newest_pricelog=newest_pricelog)


def create_online_postage_dict_list(
    db: Session, pstorepos: htmlparse.ParseStorePostage
):
    pos_dict_list: list[dict] = []
    if not pstorepos.target_prefectures:
        pref_id = const_value.NONE_PREF_ID
        for terms in pstorepos.terms:
            pos_dict: dict = {}
            pos_dict["boundary"] = terms.boundary
            pos_dict["postage"] = terms.postage
            pos_dict["pref_id"] = pref_id
            pos_dict["campaign_msg"] = pstorepos.campaign_msg
            pos_dict["insert_proc_type"] = posd.InsertProcType.ITEM_UPDATE.value
            pos_dict_list.append(pos_dict)
    else:
        pref_list = store.PrefectureQuery.get_all(db)
        pref_dict: dict[str, int] = {pref.name: pref.pref_id for pref in pref_list}
        for pref_name in pstorepos.target_prefectures:
            for terms in pstorepos.terms:
                pos_dict: dict = {}
                pos_dict["boundary"] = terms.boundary
                pos_dict["postage"] = terms.postage
                pos_dict["pref_id"] = pref_dict[pref_name]
                pos_dict["campaign_msg"] = pstorepos.campaign_msg
                pos_dict["insert_proc_type"] = posd.InsertProcType.ITEM_UPDATE.value
                pos_dict_list.append(pos_dict)
    return pos_dict_list


def add_online_storepostage(
    db: Session, pstorepos: htmlparse.ParseStorePostage, shop_id: int | None = None
):
    if not shop_id:
        shop_id = store.OnlineStoreQuery.get_shop_id(
            db=db, storename=pstorepos.storename
        )
        if not shop_id:
            raise ValueError("shop_id is None")
    pos_dict_list = create_online_postage_dict_list(db=db, pstorepos=pstorepos)
    store.OnlineStoreQuery.add_postage_by_dict_list(
        db=db,
        shop_id=shop_id,
        start_terms_id=const_value.INIT_TERMS_ID,
        pos_dict_list=pos_dict_list,
    )


def add_online_store_and_storepostage(
    db: Session, pstorepos: htmlparse.ParseStorePostage
):
    if not pstorepos:
        return
    shop_id = store.OnlineStoreQuery.add_store(db=db, storename=pstorepos.storename)
    add_online_storepostage(db=db, pstorepos=pstorepos, shop_id=shop_id)


def create_storename_to_pstorepos_dict(parseitems: htmlparse.ParseItems):
    store_to_pstorepos: dict[str, htmlparse.ParseStorePostage] = {}
    for pstorepos in parseitems.getPostageList():
        store_to_pstorepos[pstorepos.storename] = pstorepos
    return store_to_pstorepos


def create_storename_to_online_dbdata_dict(db: Session, storename_list: list[str]):
    storename_list = store.OnlineStoreQuery.get_storename_list(db)
    dbdata_list = store.OnlineStoreQuery.get_postage_including_none_by_storename_list(
        db=db,
        storename_list=storename_list,
        insert_proc_type_list=[posd.InsertProcType.ITEM_UPDATE.value],
    )
    dbdata_store_dict: dict[str, list[dict]] = {}
    for dbdata in dbdata_list:
        dic = {k: v for k, v in dbdata._mapping.items()}
        if "storename" not in dic:
            continue
        if "storename" in dbdata_store_dict:
            dbdata_store_dict[dic["storename"]].append(dic)
        else:
            dbdata_store_dict[dic["storename"]] = [dic]
    for storename in storename_list:
        if storename not in dbdata_store_dict:
            dbdata_store_dict[storename] = []
    return dbdata_store_dict


def equal_dbdata_and_online_terms(dbdata: dict, parsedata: htmlparse.ParseStorePostage):
    for terms in parsedata.terms:
        if (
            terms.boundary == dbdata["boundary"]
            and terms.postage == int(dbdata["postage"])
            and parsedata.campaign_msg == dbdata["campaign_msg"]
            and posd.InsertProcType.ITEM_UPDATE.value == int(dbdata["insert_proc_type"])
            and isLocalToday(utcTolocaltime(dbdata["created_at"]))
        ):
            return True
    return False


class NextActOnlineUpdate(Enum):
    ADD = auto()
    UPDATE = auto()
    NONE = auto()


def get_next_act_to_online_storepostage(
    parsedata: htmlparse.ParseStorePostage, dbdata_list: list[dict]
) -> NextActOnlineUpdate:
    if parsedata.target_prefectures:
        raise ValueError("ParseStorePostage.target_prefectures is not None")
    pref_id = const_value.NONE_PREF_ID
    for dbdata in dbdata_list:
        if parsedata.storename != dbdata["storename"]:
            continue
        if dbdata["pref_id"] is None:
            if parsedata.terms:
                return NextActOnlineUpdate.UPDATE
            else:
                return NextActOnlineUpdate.NONE
        if pref_id == int(dbdata["pref_id"]):
            if equal_dbdata_and_online_terms(dbdata, parsedata):
                return NextActOnlineUpdate.NONE
            return NextActOnlineUpdate.UPDATE
    return NextActOnlineUpdate.ADD


def is_fix_postage_of_campaign(pstorepos: htmlparse.ParseStorePostage):
    return (
        len(pstorepos.campaign_msg) > 0
        and len(pstorepos.terms) > 0
        and not pstorepos.target_prefectures
    )


def update_online_storepostage(db: Session, parseitems: htmlparse.ParseItems):
    if not parseitems.hasPostage():
        return
    storename_to_pstorepos = create_storename_to_pstorepos_dict(parseitems=parseitems)

    storename_to_dbdata = create_storename_to_online_dbdata_dict(
        db=db, storename_list=list(storename_to_pstorepos.keys())
    )
    for storename, pstorepos in storename_to_pstorepos.items():
        if storename in storename_to_dbdata:
            nextact = get_next_act_to_online_storepostage(
                pstorepos, storename_to_dbdata[storename]
            )
            match nextact:
                case NextActOnlineUpdate.NONE:
                    continue
                case NextActOnlineUpdate.ADD:
                    if is_fix_postage_of_campaign(pstorepos=pstorepos):
                        store.OnlineStoreQuery.delete_postage_by_storename_and_pref_id(
                            db,
                            storename=storename,
                            pref_id=const_value.NONE_PREF_ID,
                            insert_proc_type_list=[
                                posd.InsertProcType.MAKEPURE_TOOL.value
                            ],
                        )
                    add_online_storepostage(db=db, pstorepos=pstorepos, shop_id=None)
                    continue
                case NextActOnlineUpdate.UPDATE:
                    store.OnlineStoreQuery.delete_postage_by_storename_and_pref_id(
                        db=db,
                        storename=storename,
                        pref_id=const_value.NONE_PREF_ID,
                        insert_proc_type_list=[posd.InsertProcType.ITEM_UPDATE.value],
                    )
                    add_online_storepostage(db=db, pstorepos=pstorepos, shop_id=None)
                    continue
        else:
            add_online_store_and_storepostage(db=db, pstorepos=pstorepos)


def is_update_makepure_postage_shop(
    up_data: htmlparse.ParseShopIDInfo,
    db_data: store.DailyOnlineShopInfo,
    now: datetime.datetime,
):
    if up_data.storename != db_data.shop_name:
        return True
    if up_data.url != db_data.url:
        return True
    if db_data.insert_proc_type != posd.InsertProcType.ITEM_UPDATE.value:
        return True
    if utcTolocaltime(db_data.created_at).date() < utcTolocaltime(now).date():
        return True
    return False


def create_DailyOnlineShopInfo_from_ParseShopIDInfo(
    psii: htmlparse.ParseShopIDInfo, now: datetime.datetime
):
    return store.DailyOnlineShopInfo(
        shop_id=psii.shop_id,
        shop_name=psii.storename,
        url=psii.url,
        insert_proc_type=posd.InsertProcType.ITEM_UPDATE.value,
        created_at=now,
    )


def update_makepure_postage_shop_list(db: Session, parseitems: htmlparse.ParseItems):
    if not parseitems.hasShopIDInfo():
        return
    db_list = store.DailyOnlineShopInfoQuery.get_all(db=db) or []
    db_dict: dict = {dosi.shop_id: dosi for dosi in db_list}
    add_list: list[store.DailyOnlineShopInfo] = []
    up_list: list[store.DailyOnlineShopInfo] = []
    now = get_now_db_datetime()
    for psii in parseitems.getShopIDInfo().values():
        if psii.shop_id not in db_dict:
            add_list.append(create_DailyOnlineShopInfo_from_ParseShopIDInfo(psii, now))
        elif is_update_makepure_postage_shop(
            up_data=psii, db_data=db_dict[psii.shop_id], now=now
        ):
            up_list.append(create_DailyOnlineShopInfo_from_ParseShopIDInfo(psii, now))
    if up_list:
        store.DailyOnlineShopInfoQuery.update(db=db, update_list=up_list)
    if add_list:
        store.DailyOnlineShopInfoQuery.add_all(db=db, add_list=add_list)


def inactive_url(db: Session, url_id: int):
    UrlQuery.update_url_active_by_url_id(
        db=db, url_id=url_id, isactive=UrlActive.INACTIVE
    )


def get_now_db_datetime():
    dt_now = datetime.datetime.now(datetime.timezone.utc)
    date = dt_now.replace(microsecond=0)
    return date


def get_parse_data(fname: str, url_id: int, url: str):
    date = get_now_db_datetime()
    itemparseoptions = read_config.get_item_parse_options()
    return gethtmlparse.getParser(fname, url_id, date, url, itemparseoptions)


def startParse(db: Session, url: str, item_id: int, fname: str, logger=None) -> None:
    url_id = UrlQuery.add_url(db, urlpath=url)
    try:
        gp = get_parse_data(fname, url_id, url)
    except FileNotFoundError as e:
        logprint(
            text=f"{type(e)} fname={fname}, url_id={url_id}, url={url}",
            isError=True,
            logger=logger,
        )
        return
    except AttributeError as e:
        logprint(text=f"{type(e)} url={url}, {e}", isError=True, logger=logger)
        return
    except Exception as e:
        logprint(text=f"{e}", isError=True, logger=logger)
        return
    if gp is None:
        logprint(text="ERROR UNSUPPORTED URL", isError=True, logger=logger)
        return
    if gp.isDeleted():
        logprint(
            text=f"Item has been removed. inactive the url. url_id={url_id}, url={url}",
            isError=False,
            logger=logger,
        )
        inactive_url(db=db, url_id=url_id)
    else:
        update_itemsprices(db=db, parseitems=gp, item_id=item_id, url_id=url_id)
        update_online_storepostage(db=db, parseitems=gp)
        update_makepure_postage_shop_list(db=db, parseitems=gp)
    deleteTempFile(fname)

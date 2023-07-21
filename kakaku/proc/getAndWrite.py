import os
import sys
import datetime

from typing import Dict, List, Optional

from distutils.util import strtobool

from accessor.item import (
    NewestQuery,
    ItemQuery,
    UrlQuery,
)
from accessor import store
from html_parser import (
    gethtmlparse,
    htmlparse,
)
from common import read_config, const_value
from common.util import isLocalToday, utcTolocaltime
#from common.stop_watch import stop_watch


def deleteTempFile(fname):
    isAutoDel = read_config.is_auto_del_dl_file()
    if type(isAutoDel) is str:
        isAutoDel = strtobool(isAutoDel)
    if isAutoDel:
        os.remove(fname)

def logprint(text, isError, logger=None):
    if logger == None:
        print(text)
        return
    elif isError:
        logger.error(__file__ + " " + text)
        return
    else:
        logger.info(__file__+ " " + text)
        return

def getLowestPrice(an :int, bn :int):
    if an == const_value.INIT_PRICE:
        return bn
    if bn == const_value.INIT_PRICE:
        return an
    if an < bn:
        return an
    return bn

def get_oldprice(item_id :int = const_value.NONE_ID,
                 url_id :int = const_value.NONE_ID
                 ):
    if item_id > const_value.NONE_ID:
        oldprice = ItemQuery.get_most_recent_old_price_of_2days_by_item_id(item_id=item_id)
        if oldprice:
            return oldprice
        return const_value.INIT_PRICE
    if url_id > const_value.NONE_ID:
        oldprice = ItemQuery.get_most_recent_old_price_of_2days_by_url_id(url_id=url_id)
        if oldprice:
            return oldprice
        return const_value.INIT_PRICE
    return const_value.INIT_PRICE

def convert_newestitem(pddict) -> Dict:
    ret = {
        "url_id":pddict["url_id"],
        "created_at":pddict["created_at"],
        "newestprice":getLowestPrice(pddict["usedprice"], pddict["newprice"]),
        "taxin":pddict["taxin"],
        "onsale":pddict["onsale"],
        "salename":pddict["salename"],
        "trendrate":pddict["trendrate"],
        "storename":pddict["storename"],
    }
    return ret

def convert_pricelog(pddict) -> Dict:
    ret = pddict.copy()
    del ret['oldprice']
    return ret


def update_newestitem(pddict):
    if pddict is None:
        return
    nidict = convert_newestitem(pddict)
    NewestQuery.update_items_by_dict(nidict)

def update_itemsname(url_id :int, uniqname :str):
    ItemQuery.update_items_name_by_url_id(url_id, uniqname)

def update_stores(storename_list :List[str]):
    add_storename_list = get_add_storename(storename_list)
    store.StoreQuery.add_storename_list(add_storename_list)
    #if storename:
        #store.StoreQuery.add_store(storename)

def combine_duplicates_item(parseitems :htmlparse.ParseItems):
    items = parseitems.getItems()
    if len(items) == 1:
        return items
    dup_dict :Dict[str, htmlparse.ParseItemInfo] = {}
    for item in items:
        if not item.storename in dup_dict:
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

def is_combine_price(cur :int, insert :int):
    if cur == const_value.INIT_PRICE\
        and insert != const_value.INIT_PRICE:
        return True
    if cur != const_value.INIT_PRICE\
        and insert != const_value.INIT_PRICE\
        and cur > insert:
        return True
    return False

def update_itemsprices(parseitems :htmlparse.ParseItems, item_id :int, url_id :int):
    if item_id and int(item_id) != const_value.NONE_ID:
        oldprice = get_oldprice(item_id=item_id)
    else:
        oldprice = get_oldprice(url_id=url_id)
    pricelog_list = ItemQuery.get_pricelog_2days_by_url_id(url_id=url_id)
    storename_list = []
    items = combine_duplicates_item(parseitems=parseitems)
    is_update_itemsname = False
    lowest_pricedatadict = None
    for pd in items:
            pd.oldPrice = oldprice
            pricedatadict = pd.getOrderedDict()
            if not is_update_itemsname:
                is_update_itemsname = True
                update_itemsname(pricedatadict["url_id"], pricedatadict["uniqname"])
            update_itemsprice(pricedatadict, pricelog_list)
            storename_list.append(pricedatadict['storename'])
            lowest_pricedatadict = min_pricedatadict(lowest_pricedatadict, pricedatadict)
            continue
    update_newestitem(lowest_pricedatadict)
    update_stores(storename_list)

def min_pricedatadict(p1 :Optional[Dict], p2 :Dict):
    if p1 is None:
        return p2
    else:
        lowestprice = getLowestPrice(p2['usedprice'], p2['newprice'])
        if lowestprice != const_value.INIT_PRICE:
            p1_lowest = getLowestPrice(p1['usedprice'], p1['newprice'])
            if p1_lowest == const_value.INIT_PRICE:
                return p2
            if lowestprice < p1_lowest:
                return p2
    return p1

def get_add_storename(storename_list :List[str]):
    add_list = []
    db_storename_list = [s.storename for s in store.StoreQuery.get_all()]
    for storename in storename_list:
        if not storename in db_storename_list:
            add_list.append(storename)
    return add_list
#@stop_watch
def upsert_pricelog(pldict :Dict, newest_pricelog):
    if newest_pricelog\
        and isLocalToday(utcTolocaltime(newest_pricelog.created_at)):
        if __is_update_price(insert_new=pldict['newprice'],
                              insert_used=pldict['usedprice'],
                              db_new=newest_pricelog.newprice,
                              db_used=newest_pricelog.usedprice):
            ItemQuery.update_pricelog_2days_by_dict_and_log_id(pldict=pldict,
                                                           log_id=newest_pricelog.log_id)
            return True
        if __is_add_price(insert_new=pldict['newprice'],
                              insert_used=pldict['usedprice'],
                              db_new=newest_pricelog.newprice,
                              db_used=newest_pricelog.usedprice):
            ItemQuery.add_pricelog_2days_by_dict(pldict)
            return True
        return False
    else:
        ItemQuery.add_pricelog_2days_by_dict(pldict)
        return True

def __is_add_price(insert_new :int,
                   insert_used :int,
                   db_new :int,
                   db_used:int):
    if insert_new == db_new\
        and insert_used == db_used:
        return False
    return True

def __is_update_price(insert_new :int,
                      insert_used :int,
                      db_new :int,
                      db_used:int):
    if db_new == const_value.INIT_PRICE\
        and insert_new != const_value.INIT_PRICE\
        and insert_used == db_used:
        return True
    if db_used == const_value.INIT_PRICE\
        and insert_used != const_value.INIT_PRICE\
        and insert_new == db_new:
        return True
    return False
    #if (insert_new != db_new and insert_new != const_value.INIT_PRICE)\
    #    or (insert_used != db_used and insert_used != const_value.INIT_PRICE):
    #    return True
    #return False

def get_newest_pricelog(pricelog_list :List, url_id :int, storename :str):
    newest = None
    for pricelog in pricelog_list:
        if pricelog.url_id != url_id\
            or pricelog.storename != storename:
            continue
        if newest is None:
            newest = pricelog
            continue
        elif newest.created_at < pricelog.created_at:
            newest = pricelog
        continue
    return newest

#@stop_watch
def update_itemsprice(pricedatadict :Dict,
                      pricelog_list :List):
    newest_pricelog = get_newest_pricelog(pricelog_list,
                                          pricedatadict['url_id'],
                                          pricedatadict['storename'])
    pldict = convert_pricelog(pricedatadict)
    upsert_pricelog(pldict, newest_pricelog)

def get_parse_data(fname, url_id, url):
    dt_now = datetime.datetime.utcnow()
    date = dt_now.replace(microsecond = 0)
    return gethtmlparse.getParser(fname, url_id, date, url)
    
def startParse(url :str, item_id, fname :str, logger=None) -> None:
    url_id = UrlQuery.add_url(url)
    gp = get_parse_data(fname, url_id, url)
    if gp is None:
        logprint("ERROR UNSUPPORTED URL", True, logger)
        return
    update_itemsprices(parseitems=gp, item_id=item_id, url_id=url_id)
    deleteTempFile(fname)

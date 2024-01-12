
import requests

from common import const_value as cmn_const_value
from itemcomb.surugaya_postage.parse_makepure import SurugayaMakepure
from itemcomb.surugaya_postage.const_value import (
    header,
    SHOPLIST_URL,
)
from downloader import download_html
from itemcomb.postage_data import InsertProcType

from accessor.read_sqlalchemy import Session
from accessor.store import (
    DailyOnlineShopInfoQuery,
    DailyOnlineShopInfo
)

def downLoadHtml(url):
    res = requests.get(url=url, headers=header, cookies=None, timeout=(3.5, 7.0))
    if res.status_code != requests.codes.ok :
        print('Error Status Code ' + str(res.status_code))
        return
    res.encoding = res.apparent_encoding
    text = res.text
    return text

def getMakepureHtml():
    ok, res = download_html.getUrlHtml(SHOPLIST_URL)
    return res


def is_todays_data_dailyonlineshopinfo(db :Session):
    cnt = DailyOnlineShopInfoQuery.get_todays_count(db=db,
                                                    insert_proc_type_list=[InsertProcType.MAKEPURE_TOOL.value]
                                                    )
    if cnt and cnt > 0:
        return True
    return False

def is_expired_dailyonlineshopinfo(db :Session):
    cnt = DailyOnlineShopInfoQuery.get_count_before_today(db=db,
                                                    insert_proc_type_list=[InsertProcType.MAKEPURE_TOOL.value]
                                                    )
    if cnt and cnt > 0:
        return True
    return False


def create_db_shop_id_dict(db :Session):
    db_data = DailyOnlineShopInfoQuery.get_all(db=db) or []
    results :dict[int, int] = {}
    for dosi in db_data:
        if dosi.shop_id in results:
            continue
        results[dosi.shop_id] = 1
    return results

def create_dailyonlineshopinfo(db :Session):
    DailyOnlineShopInfoQuery.delete(db=db,
                                    insert_proc_type_list=[InsertProcType.MAKEPURE_TOOL.value]
                                    )
    sm = SurugayaMakepure()
    sm.parse(getMakepureHtml(), insert_proc_type=InsertProcType.MAKEPURE_TOOL.value)
    dic = sm.getShopDict()
    add_list :list[DailyOnlineShopInfo] = []
    dup_chk :dict = {}
    db_shopid_dict = create_db_shop_id_dict(db)
    
    for v in dic.values():
        shop_id = int(v["shop_id"])
        if shop_id in dup_chk:
            continue
        dup_chk[shop_id] = 1
        if shop_id in db_shopid_dict:
            continue
        add_list.append(DailyOnlineShopInfo(
            shop_id=int(v["shop_id"]),
            shop_name=v["shop_name"],
            url=v["url"],
            insert_proc_type=v["insert_proc_type"]
            )
            )
    DailyOnlineShopInfoQuery.add_all(db=db, add_list=add_list)


def grepShopList(db :Session, name :str):
    ret = DailyOnlineShopInfoQuery.get_by_contains_storename(db, storename=name)
    if not ret:
        return []
    results :list[dict] = []
    for r in ret:
        results.append(r.toDict())
    return results

def getShopID(db :Session, name:str) -> int:
    ret = DailyOnlineShopInfoQuery.get_shop_id_by_storename(db, storename=name)
    if not ret:
        return cmn_const_value.NONE_ID
    return ret



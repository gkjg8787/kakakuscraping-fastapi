import os
import re
from datetime import datetime, timezone
import difflib

from accessor.read_sqlalchemy import Session
from accessor import store
from itemcomb import surugaya_postage_util as spu
from itemcomb import prefecture, postage_data as posd
from common import cmnlog, const_value
from downloader import download_html
from html_parser import (
    htmlparse,
    surugaya_html_parse,
    netoff_html_parse,
    bookoff_html_parse,
    geo_html_parse,
)


def get_filename():
    return os.path.basename(__file__)


def getLogger():
    return cmnlog.getLogger(cmnlog.LogName.PARSE)


def get_db_postage_dict(db: Session, storename_list: list[str]):
    db_pos_list = store.OnlineStoreQuery.get_postage_including_none_by_storename_list(
        db=db,
        storename_list=storename_list,
        insert_proc_type_list=[
            posd.InsertProcType.ITEM_UPDATE.value,
            posd.InsertProcType.MAKEPURE_TOOL.value,
        ],
    )
    if not db_pos_list:
        return {}
    res_dict_list: dict[str, list[dict]] = {}
    for r in db_pos_list:
        dic = dict(r._mapping.items())
        stname = dic["storename"]
        if stname in res_dict_list:
            res_dict_list[stname].append(dic)
        else:
            res_dict_list[stname] = [dic]
    return res_dict_list


class PrefInfo:
    name_to_id: dict[str, int]
    id_to_name: dict[int, str]

    def __init__(self, db: Session):
        self.name_to_id = {}
        self.id_to_name = {}
        db_ret = store.PrefectureQuery.get_all(db=db)
        if not db_ret:
            return
        for p in db_ret:
            self.name_to_id[p.name] = p.pref_id
            self.id_to_name[p.pref_id] = p.name

    def get_name(self, id: int):
        if id not in self.id_to_name:
            return None
        return self.id_to_name[id]

    def get_id(self, name: str):
        if name not in self.name_to_id:
            return None
        return self.name_to_id[name]


def get_upper_limit_of_common(db_dict_list: dict):
    for db_dic in db_dict_list:
        if db_dic["pref_id"] is None:
            continue
        if int(db_dic["pref_id"]) != const_value.NONE_PREF_ID:
            continue
        if int(db_dic["postage"]) != 0:
            continue
        if ":" in db_dic["boundary"]:
            continue
        ret = posd.ShippingTermsBoundary.get_list_of_boundary_value_and_operation(
            db_dic["boundary"]
        )
        if not ret:
            continue
        if int(ret[0]["boundary_val"]) == 0:
            continue
        limit_ope = posd.ShippingTermsBoundary.reverse_operator(ret[0]["boundary_ope"])
        return {"boundary_ope": limit_ope, "boundary_val": ret[0]["boundary_val"]}
    return {}


def get_db_data_by_pref_id(pref_id: int, db_dict_list: list[dict]):
    results: list = []
    for db_dic in db_dict_list:
        if db_dic["pref_id"] is None:
            continue
        if pref_id == int(db_dic["pref_id"]):
            results.append(db_dic)
    return results


def get_terms_id_of_same_terms(
    db_dict_list: list[dict],
    boundary: str,
    postage: int,
):
    for db_dic in db_dict_list:
        if not db_dic["boundary"]:
            continue
        if int(db_dic["postage"]) != postage:
            continue
        if db_dic["boundary"] != boundary:
            continue
        return int(db_dic["terms_id"])
    return None


def create_common_fixed_boundary(storename_db_dict: dict):
    upper_limit_for_update = get_upper_limit_of_common(db_dict_list=storename_db_dict)
    pref_common_boundary = {"boundary_ope": "<=", "boundary_val": 0}
    if upper_limit_for_update:
        return posd.ShippingTermsBoundary.create_boundary_of_db(
            lower_ope=pref_common_boundary["boundary_ope"],
            lower_val=pref_common_boundary["boundary_val"],
            upper_ope=upper_limit_for_update["boundary_ope"],
            upper_val=upper_limit_for_update["boundary_val"],
        )
    return posd.ShippingTermsBoundary.create_boundary_of_db(
        lower_ope=pref_common_boundary["boundary_ope"],
        lower_val=pref_common_boundary["boundary_val"],
    )


def create_pos_dict(
    pref_id: int,
    boundary: str,
    postage: int,
    terms_id: int | None = None,
    created_at: datetime | None = None,
):
    add_db_data: dict = {}
    add_db_data["boundary"] = boundary
    add_db_data["postage"] = postage
    add_db_data["pref_id"] = pref_id
    add_db_data["campaign_msg"] = ""
    add_db_data["insert_proc_type"] = posd.InsertProcType.MAKEPURE_TOOL.value
    if terms_id:
        add_db_data["terms_id"] = terms_id
    if created_at:
        add_db_data["created_at"] = created_at
    return add_db_data


def get_update_data_near_storename(
    storename: str,
    update_data_list: list[spu.StoreShippingInfo],
):
    update_data = update_data_list[0]
    near_r = 0
    base_r = 1.0
    for upd in update_data_list:
        r = difflib.SequenceMatcher(None, storename, upd.shop_name)
        if r.ratio() == base_r:
            update_data = upd
            break
        if r.ratio() > near_r:
            update_data = upd
            near_r = r.ratio()
    return update_data


def update_after_confirming(
    db: Session,
    storename: str,
    db_dict: dict,
    prefinfo: PrefInfo,
    update_data_list: list[spu.StoreShippingInfo],
    logger: cmnlog.logging.Logger,
):
    if len(update_data_list) > 1:
        shopnames = [upd.shop_name for upd in update_data_list]
        logger.warning(
            f"{get_filename()}"
            f" get online store postage many len={len(update_data_list)}, searchword={storename}, shopname={shopnames}"
        )
        update_data = get_update_data_near_storename(storename, update_data_list)
    else:
        update_data = update_data_list[0]

    if not update_data.prefectures_postage:
        logger.warning(
            f"{get_filename()}"
            f" no prefectures postage, shop_id={update_data.shop_id}, shop_name={update_data.shop_name}"
        )
        return
    common_fixed_boundary = create_common_fixed_boundary(
        storename_db_dict=db_dict[storename]
    )
    add_db_data_list: list[dict] = []
    update_db_data_list: list[dict] = []
    delete_db_data_set: set[int] = []
    nowdate = datetime.now(timezone.utc)
    for prefpos in update_data.prefectures_postage:
        pref_id = prefinfo.get_id(prefpos.name)
        if prefpos.get_postage() is None:
            continue
        pref_db_data_list = get_db_data_by_pref_id(
            pref_id=pref_id, db_dict_list=db_dict[storename]
        )
        same_terms_id = get_terms_id_of_same_terms(
            db_dict_list=pref_db_data_list,
            boundary=common_fixed_boundary,
            postage=prefpos.get_postage(),
        )
        if same_terms_id:
            continue
        if pref_db_data_list:
            if (
                len(pref_db_data_list) == 1
                and pref_db_data_list[0]["insert_proc_type"]
                == posd.InsertProcType.MAKEPURE_TOOL.value
            ):
                update_db_data_list.append(
                    create_pos_dict(
                        pref_id=pref_id,
                        boundary=common_fixed_boundary,
                        postage=prefpos.get_postage(),
                        terms_id=pref_db_data_list[0]["terms_id"],
                        created_at=nowdate,
                    )
                )
                continue
            if len(pref_db_data_list) > 1:
                count = 0
                target_terms_id = None
                for pref_db_data in pref_db_data_list:
                    if (
                        pref_db_data["insert_proc_type"]
                        == posd.InsertProcType.MAKEPURE_TOOL.value
                    ):
                        count += 1
                        target_terms_id = pref_db_data["terms_id"]
                if count == 1:
                    update_db_data_list.append(
                        create_pos_dict(
                            pref_id=pref_id,
                            boundary=common_fixed_boundary,
                            postage=prefpos.get_postage(),
                            terms_id=target_terms_id,
                            created_at=nowdate,
                        )
                    )
                    continue
                if count > 1:
                    delete_db_data_set.add(pref_id)
                    add_db_data_list.append(
                        create_pos_dict(
                            pref_id=pref_id,
                            boundary=common_fixed_boundary,
                            postage=prefpos.get_postage(),
                        )
                    )
                    continue

        add_db_data_list.append(
            create_pos_dict(
                pref_id=pref_id,
                boundary=common_fixed_boundary,
                postage=prefpos.get_postage(),
            )
        )

    shop_id = store.OnlineStoreQuery.get_shop_id(db=db, storename=storename)
    if delete_db_data_set:
        store.OnlineStoreQuery.delete_postage_by_shop_id_and_pref_id_list_and_insert_proc_type(
            db=db,
            shop_id=shop_id,
            pref_id_list=list(delete_db_data_set),
            insert_proc_type=posd.InsertProcType.MAKEPURE_TOOL.value,
        )
    if update_db_data_list:
        store.OnlineStoreQuery.update_postage_by_dict_list(
            db=db, shop_id=shop_id, pos_dict_list=update_db_data_list
        )
    if add_db_data_list:
        store.OnlineStoreQuery.add_postage_by_dict_list(
            db=db,
            shop_id=shop_id,
            start_terms_id=const_value.NONE_PREF_ID,
            pos_dict_list=add_db_data_list,
        )


def needs_update_by_campaign_msg(db_list: list[dict], prefinfo: PrefInfo):
    fix_ptn = re.compile(r"([1-9][0-9]+)円?(未満)\s+?([1-9][0-9]+)円?[^～]")
    range_ptn = re.compile(
        r"([1-9][0-9]+)円?(未満)\s+?([1-9][0-9]+)円?～([1-9][0-9]+)円?"
    )
    for db_data in db_list:
        if not db_data["campaign_msg"]:
            continue
        if not db_data["pref_id"]:
            continue
        if (
            prefinfo.get_name(int(db_data["pref_id"]))
            != prefecture.PrefectureName.get_country_wide_name()
        ):
            continue
        target_text = str(db_data["campaign_msg"]).replace(",", "")
        m = re.findall(range_ptn, target_text)
        if m:
            return True
        m = re.findall(fix_ptn, target_text)
        if not m:
            return True
        return False
    return True


def update_surugaya_makepure_store_postage(
    db: Session, sn_list: list[str], logger: cmnlog.logging.Logger
):
    pref_list = prefecture.PrefectureName.get_all_prefecturename()
    db_dict = get_db_postage_dict(db=db, storename_list=sn_list)
    prefinfo = PrefInfo(db)
    skip_storenames = ["駿河屋", "ゲオ", "ブックオフ", "ネットオフ"]
    online_update_post_wait_time = 1
    for storename in sn_list:
        if storename in skip_storenames:
            continue
        if storename not in db_dict:
            logger.warning(
                f"{get_filename()}"
                f" not match storename in db data, storename={storename}"
            )
            continue
        if not needs_update_by_campaign_msg(db_dict[storename], prefinfo=prefinfo):
            continue
        rets = spu.get_shippingResult(
            db=db,
            storename=storename,
            prefectures=pref_list,
            post_wait_time=online_update_post_wait_time,
            exact=True,
        ).get_list()
        if not rets:
            logger.warning(
                f"{get_filename()} not result of makepure tool storename={storename}"
            )
            continue
        update_after_confirming(
            db=db,
            storename=storename,
            db_dict=db_dict,
            prefinfo=prefinfo,
            update_data_list=rets,
            logger=logger,
        )


def create_postage_dict_list(
    db: Session,
    psp_list: list[surugaya_html_parse.htmlparse.ParseStorePostage],
    insert_proc_type: posd.InsertProcType,
):
    pos_dict_list: list[dict] = []
    pref_dict: dict[str, int] = {
        pref.name: pref.pref_id for pref in store.PrefectureQuery.get_all(db)
    }
    for psp in psp_list:
        if not psp.target_prefectures:
            pref_id = const_value.NONE_PREF_ID
            for terms in psp.terms:
                pos_dict: dict = {}
                pos_dict["boundary"] = terms.boundary
                pos_dict["postage"] = terms.postage
                pos_dict["pref_id"] = pref_id
                pos_dict["campaign_msg"] = psp.campaign_msg
                pos_dict["insert_proc_type"] = insert_proc_type.value
                pos_dict_list.append(pos_dict)
        else:
            for pref_name in psp.target_prefectures:
                for terms in psp.terms:
                    pos_dict: dict = {}
                    pos_dict["boundary"] = terms.boundary
                    pos_dict["postage"] = terms.postage
                    pos_dict["pref_id"] = pref_dict[pref_name]
                    pos_dict["campaign_msg"] = psp.campaign_msg
                    pos_dict["insert_proc_type"] = insert_proc_type.value
                    pos_dict_list.append(pos_dict)
    return pos_dict_list


def get_and_update_specific_url(
    db: Session,
    logger: cmnlog.logging.Logger,
    url: str,
    parser,
    insert_proc_type: posd.InsertProcType,
):
    ok, res = download_html.getUrlHtml(url)
    if not ok:
        logger.warning(f"{get_filename} fail download {url} ,{res}")
        return
    p = parser(res)
    if not hasattr(p, "get_ParseStorePostage"):
        raise AttributeError("fail calling parser of get_ParseStorePostage")
    sp_list: list[htmlparse.ParseStorePostage] = parser(res).get_ParseStorePostage()
    if not sp_list:
        logger.warning(f"{get_filename} not get postage of {url}")
        return
    storename = sp_list[0].storename
    shop_id = store.OnlineStoreQuery.get_shop_id(db, storename=storename)
    if not shop_id:
        shop_id = store.OnlineStoreQuery.add_store(db, storename=storename)
    store.OnlineStoreQuery.delete_postage_by_shop_id_and_insert_proc_type(
        db=db, shop_id=shop_id, insert_proc_type=insert_proc_type.value
    )
    pos_dict_list = create_postage_dict_list(
        db=db, psp_list=sp_list, insert_proc_type=insert_proc_type
    )
    store.OnlineStoreQuery.add_postage_by_dict_list(
        db=db,
        shop_id=shop_id,
        start_terms_id=const_value.INIT_TERMS_ID,
        pos_dict_list=pos_dict_list,
    )


def update_store_of_specific_url(
    db: Session,
    logger: cmnlog.logging.Logger,
):
    update_stores = {
        "surugaya": {
            "url": "https://www.suruga-ya.jp/man/qa/hanbai_qa/shiharai.html",
            "parser": surugaya_html_parse.SurugayaShiharaiParse,
            "insert_proc_type": posd.InsertProcType.SURUGAYA_MAILORDER_FEE,
        },
        "netoff": {
            "url": "https://www.netoff.co.jp/guide/delivery.jsp",
            "parser": netoff_html_parse.NetoffDeliveryParse,
            "insert_proc_type": posd.InsertProcType.NETOFF_SHIPPING_SURCHARGE,
        },
        "bookoff": {
            "url": "https://www.bookoffonline.co.jp/files/user-guide/order.html",
            "parser": bookoff_html_parse.BookoffOrderParse,
            "insert_proc_type": posd.InsertProcType.BOOKOFF_SHIPPING_TERMS,
        },
        "geo": {
            "url": "https://ec.geo-online.co.jp/shop/pages/guide.aspx",
            "parser": geo_html_parse.GeoGuideParse,
            "insert_proc_type": posd.InsertProcType.GEO_SHIPPING_TERMS,
        },
    }
    for name, val in update_stores.items():
        logger.info(f"{get_filename()} update {name} specific url")
        get_and_update_specific_url(
            db,
            logger=logger,
            url=val["url"],
            parser=val["parser"],
            insert_proc_type=val["insert_proc_type"],
        )


def update_online_store_postage(db: Session):
    logger = getLogger()
    logger.info(f"{get_filename()} start update_onilne_store_postage")
    sn_list: list[str] = store.OnlineStoreQuery.get_todays_storenames(db=db)
    if not sn_list:
        logger.info(f"{get_filename()} no today's storename")
        return
    sn_list = list(dict.fromkeys(sn.strip() for sn in sn_list))
    logger.info(f"{get_filename()} delete old store postage")
    store.OnlineStoreQuery.delete_postage(db=db, delete_older_than_today=True)
    store.OnlineStoreQuery.delete_postage_by_not_in_storename_list(
        db=db, storename_list=sn_list
    )
    store.OnlineStoreQuery.delete_store_by_not_in_storename_list(
        db=db, storename_list=sn_list
    )
    store.DailyOnlineShopInfoQuery.delete(db=db, delete_older_than_today=True)
    logger.info(f"{get_filename()} update store postage")
    logger.info(f"{get_filename()} update surugaya makepure")
    update_surugaya_makepure_store_postage(db=db, sn_list=sn_list, logger=logger)
    update_store_of_specific_url(db=db, logger=logger)
    logger.info(f"{get_filename()} end update_onilne_store_postage")

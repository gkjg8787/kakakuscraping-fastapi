import os
import re

from accessor.read_sqlalchemy import Session
from accessor import store
from itemcomb import surugaya_postage_util as spu
from itemcomb import prefecture, postage_data as posd
from common import (
    cmnlog,
    const_value
)
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
    return cmnlog.getLogger(cmnlog.LogName.MANAGER)

def get_db_postage_dict(db :Session, storename_list :list[str]):
    db_pos_list = store.OnlineStoreQuery.get_postage_including_none_by_storename_list(db=db,
                                                                       storename_list=storename_list,
                                                                       insert_proc_type_list=[
                                                                           posd.InsertProcType.ITEM_UPDATE.value,
                                                                           posd.InsertProcType.MAKEPURE_TOOL.value
                                                                        ]
                                                                       )
    if not db_pos_list:
        return {}
    res_dict_list :dict[str, list[dict]] = {}
    for r in db_pos_list:
        dic = dict(r._mapping.items())
        stname = dic["storename"]
        if stname in res_dict_list:
            res_dict_list[stname].append(dic)
        else:
            res_dict_list[stname] = [dic]
    return res_dict_list

def get_db_prefecture_dict(db :Session):
    db_ret = store.PrefectureQuery.get_all(db=db)
    if not db_ret:
        return {}
    result :dict = {}
    for r in db_ret:
        result[r.name] = r
    return result


def get_upper_limit_of_common(db_dict_list :dict):
    for db_dic in db_dict_list:
        if db_dic["pref_id"] is None:
            continue
        if int(db_dic["pref_id"]) != const_value.NONE_PREF_ID:
            continue
        if int(db_dic["postage"]) != 0:
            continue
        if ":" in db_dic["boundary"]:
            continue
        ret = posd.ShippingTermsBoundary.get_list_of_boundary_value_and_operation(db_dic["boundary"])
        if not ret:
            continue
        if int(ret[0]["boundary_val"]) == 0:
            continue
        limit_ope = posd.ShippingTermsBoundary.reverse_operator(ret[0]["boundary_ope"])
        return {"boundary_ope":limit_ope, "boundary_val":ret[0]["boundary_val"]} 
    return {}

def get_db_data_by_pref_id(pref_id :int, db_dict_list :list[dict]):
    results :list = []
    for db_dic in db_dict_list:
        if db_dic["pref_id"] is None:
            continue
        if pref_id == int(db_dic["pref_id"]):
            results.append(db_dic)
    return results

def get_terms_id_of_same_terms(
                      db_dict_list :list[dict],
                      boundary:str,
                      postage :int,
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

def create_common_fixed_boundary(storename_db_dict :dict):
    upper_limit_for_update = get_upper_limit_of_common(db_dict_list=storename_db_dict)
    pref_common_boundary = {"boundary_ope":"<=", "boundary_val":0}
    if upper_limit_for_update:
        return posd.ShippingTermsBoundary.create_boundary_of_db(lower_ope=pref_common_boundary["boundary_ope"],
                                                        lower_val=pref_common_boundary["boundary_val"],
                                                        upper_ope=upper_limit_for_update["boundary_ope"],
                                                        upper_val=upper_limit_for_update["boundary_val"]
                                                        )
    return posd.ShippingTermsBoundary.create_boundary_of_db(lower_ope=pref_common_boundary["boundary_ope"],
                                                            lower_val=pref_common_boundary["boundary_val"],
                                                            )
        

def update_after_confirming(db :Session,
                            storename :str,
                            db_dict :dict,
                            update_data_list :list[spu.StoreShippingInfo],
                            search_word :str,
                            logger :cmnlog.logging.Logger
                            ):
    if len(update_data_list) > 1:
        # 2つ以上の店舗のデータが取得できてしまった時ログ掃き出し（検索ワードが広すぎ）
        shopnames = [upd.shop_name for upd in update_data_list]
        logger.warning(f"{get_filename()} get online store postage many len={len(update_data_list)}, searchword={search_word}, shopname={shopnames}")
    update_data = update_data_list[0]
    if not update_data.prefectures_postage:
        logger.debug(f"{get_filename()} no prefectures postage")
        return
    db_pref_dict = get_db_prefecture_dict(db=db)
    # 共通の送料無料条件があればその条件の閾値を上限として取得する
    if not storename in db_dict:
        logger.warning(f"{get_filename()} not match storename in db data, storename={storename}")
        return
    common_fixed_boundary = create_common_fixed_boundary(storename_db_dict=db_dict[storename])
    add_db_data_list :list[dict] = []
    for prefpos in update_data.prefectures_postage:
        pref_id = db_pref_dict[prefpos.name].pref_id
        #if pref_id == const_value.NONE_PREF_ID:
        #    continue
        if prefpos.get_postage() is None:
            continue
        #条件が一致するもの以外は削除し、一致するものがないなら追加
        pref_db_data_list = get_db_data_by_pref_id(pref_id=pref_id, db_dict_list=db_dict[storename])
        same_terms_id = get_terms_id_of_same_terms(
                                            db_dict_list=pref_db_data_list,
                                            boundary=common_fixed_boundary,
                                            postage=prefpos.get_postage()
                                            )
        if same_terms_id:
            if len(pref_db_data_list) == 1:
                continue
            store.OnlineStoreQuery.delete_postage_by_storename_and_pref_id_and_not_in_terms_id(
                    db=db,
                    storename=storename,
                    pref_id=pref_id,
                    leave_terms_id_list=[same_terms_id],
                    insert_proc_type_list=[posd.InsertProcType.MAKEPURE_TOOL.value]
                )
            continue
        add_db_data :dict = {}
        add_db_data["boundary"] = common_fixed_boundary
        add_db_data["postage"] = prefpos.get_postage()
        add_db_data["pref_id"] = pref_id
        add_db_data["campaign_msg"] = ""
        add_db_data["insert_proc_type"] = posd.InsertProcType.MAKEPURE_TOOL.value
        add_db_data_list.append(add_db_data)
    
    if not add_db_data_list:
        return
    shop_id = store.OnlineStoreQuery.get_shop_id(db=db, storename=storename)
    store.OnlineStoreQuery.add_postage_by_dict_list(db=db,
                                    shop_id=shop_id,
                                    start_terms_id=const_value.NONE_PREF_ID,
                                    pos_dict_list=add_db_data_list
                                    )

def update_surugaya_makepure_store_postage(db :Session,
                                           sn_list :list[str],
                                           logger :cmnlog.logging.Logger
                                           ):
    pref_list = prefecture.PrefectureName.get_all_prefecturename()
    db_dict = get_db_postage_dict(db=db, storename_list=sn_list)
    skip_storenames = ["駿河屋", "ゲオ", "ブックオフ", "ネットオフ"]
    for storename in sn_list:
        if storename in skip_storenames:
             continue
        word = spu.convert_storename_to_search_storename(storename)
        if not word:
            continue
        rets = spu.get_shippingResult(db=db, storename=word, prefectures=pref_list).get_list()
        if not rets:
            continue
        update_after_confirming(db=db,
                                storename=storename,
                                db_dict=db_dict,
                                update_data_list=rets,
                                search_word=word,
                                logger=logger
                                )

def create_postage_dict_list(db :Session,
                             psp_list :list[surugaya_html_parse.htmlparse.ParseStorePostage],
                             insert_proc_type :posd.InsertProcType
                             ):
    pos_dict_list :list[dict]= []
    pref_dict :dict[str, int] = { pref.name : pref.pref_id for pref in store.PrefectureQuery.get_all(db)}        
    for psp in psp_list:
        if not psp.target_prefectures:
            pref_id = const_value.NONE_PREF_ID
            for terms in psp.terms:
                pos_dict :dict = {}
                pos_dict["boundary"] = terms.boundary
                pos_dict["postage"] = terms.postage
                pos_dict["pref_id"] = pref_id
                pos_dict["campaign_msg"] = psp.campaign_msg
                pos_dict["insert_proc_type"] = insert_proc_type.value
                pos_dict_list.append(pos_dict)
        else:
            for pref_name in psp.target_prefectures:
                for terms in psp.terms:
                    pos_dict :dict = {}
                    pos_dict["boundary"] = terms.boundary
                    pos_dict["postage"] = terms.postage
                    pos_dict["pref_id"] = pref_dict[pref_name]
                    pos_dict["campaign_msg"] = psp.campaign_msg
                    pos_dict["insert_proc_type"] = insert_proc_type.value
                    pos_dict_list.append(pos_dict)
    return pos_dict_list

def get_and_update_specific_url(db :Session,
                                logger :cmnlog.logging.Logger,
                                url :str,
                                parser,
                                insert_proc_type :posd.InsertProcType
                                ):
    ok, res = download_html.getUrlHtml(url)
    if not ok:
        logger.warning(f"{get_filename} fail download {url} ,{res}")
        return
    p = parser(res)
    if not hasattr(p, "get_ParseStorePostage"):
        raise AttributeError(f"fail calling parser of get_ParseStorePostage")
    sp_list :list[htmlparse.ParseStorePostage] = parser(res).get_ParseStorePostage()
    if not sp_list:
        logger.warning(f"{get_filename} not get postage of {url}")
        return
    storename = sp_list[0].storename
    shop_id = store.OnlineStoreQuery.get_shop_id(db, storename=storename)
    if not shop_id:
        shop_id = store.OnlineStoreQuery.add_store(db, storename=storename)
    store.OnlineStoreQuery.delete_postage_by_shop_id_and_insert_proc_type(db=db,
                                                                   shop_id=shop_id,
                                                                   insert_proc_type=insert_proc_type.value
                                                                   )
    pos_dict_list = create_postage_dict_list(db=db, psp_list=sp_list, insert_proc_type=insert_proc_type)
    store.OnlineStoreQuery.add_postage_by_dict_list(db=db,
                                                    shop_id=shop_id,
                                                    start_terms_id=const_value.INIT_TERMS_ID,
                                                    pos_dict_list=pos_dict_list
                                                    )

def update_store_of_specific_url(db :Session,
                                 logger :cmnlog.logging.Logger,
                                 ):
    update_stores = {
        "surugaya":{
            "url":"https://www.suruga-ya.jp/man/qa/hanbai_qa/shiharai.html",
            "parser":surugaya_html_parse.SurugayaShiharaiParse,
            "insert_proc_type":posd.InsertProcType.SURUGAYA_MAILORDER_FEE,
        },
        "netoff":{
            "url":"https://www.netoff.co.jp/guide/delivery.jsp",
            "parser":netoff_html_parse.NetoffDeliveryParse,
            "insert_proc_type":posd.InsertProcType.NETOFF_SHIPPING_SURCHARGE,
        },
        "bookoff":{
            "url":"https://www.bookoffonline.co.jp/files/user-guide/order.html",
            "parser":bookoff_html_parse.BookoffOrderParse,
            "insert_proc_type":posd.InsertProcType.BOOKOFF_SHIPPING_TERMS,
        },
        "geo":{
            "url":"https://ec.geo-online.co.jp/shop/pages/guide.aspx",
            "parser":geo_html_parse.GeoGuideParse,
            "insert_proc_type":posd.InsertProcType.GEO_SHIPPING_TERMS,
        }
    }
    for name, val in update_stores.items():
        logger.info(f"{get_filename()} update {name} specific url")
        get_and_update_specific_url(db,
                                    logger=logger,
                                    url=val["url"],
                                    parser=val["parser"],
                                    insert_proc_type=val["insert_proc_type"]
                                    )

def update_online_store_postage(db :Session):
    logger = getLogger()
    logger.info(f"{get_filename()} start update_onilne_store_postage")
    sn_list :list[str] = store.OnlineStoreQuery.get_todays_storenames(db=db)
    if not sn_list:
        logger.info(f"{get_filename()} no today's storename")
        return
    sn_list = list(dict.fromkeys(sn.strip() for sn in sn_list))
    logger.info(f"{get_filename()} delete old store postage")
    store.OnlineStoreQuery.delete_postage_by_not_in_storename_list(db=db, storename_list=sn_list)
    store.DailyOnlineShopInfoQuery.delete(db=db, delete_older_than_today=True)
    logger.info(f"{get_filename()} update store postage")
    logger.info(f"{get_filename()} update surugaya makepure")
    update_surugaya_makepure_store_postage(db=db, sn_list=sn_list, logger=logger)
    update_store_of_specific_url(db=db, logger=logger)
    logger.info(f"{get_filename()} end update_onilne_store_postage")

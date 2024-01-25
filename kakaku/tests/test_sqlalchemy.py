from accessor.store import StoreQuery

from sqlalchemy import (
    insert,
    delete,
)

from model.item import (
    NewestItem,
    Item,
    UrlInItem,
    PriceLog,
    PriceLog_2days,
    Url,
    Group,
    GroupItem,
)
from model.store import (
    Store,
    StorePostage,
    Prefecture,
    OnlineStore,
    OnlineStorePostage,
    DailyOnlineShopInfo,
)


def insert_pricelog_sync(db, pldict: dict):
    insert_pricelog = insert(PriceLog).values(pldict)
    insert_pricelog_2days = insert(PriceLog_2days).values(pldict)
    db.execute(insert_pricelog)
    db.execute(insert_pricelog_2days)
    db.commit()


def insert_pricelog_dict_list_sync(db, pldict_list: list[dict]):
    insert_pricelog = insert(PriceLog).values(pldict_list)
    insert_pricelog_2days = insert(PriceLog_2days).values(pldict_list)
    db.execute(insert_pricelog)
    db.execute(insert_pricelog_2days)
    db.commit()


def insert_item_dict(db, item_dict: dict):
    stmt = insert(Item).values(item_dict)
    db.execute(stmt)
    db.commit()


def insert_item_dict_list(db, item_list: list[dict]):
    stmt = insert(Item).values(item_list)
    db.execute(stmt)
    db.commit()


def insert_newestitem_dict(db, nidict: dict):
    stmt = insert(NewestItem).values(nidict)
    db.execute(stmt)
    db.commit()


def insert_newestitem_dict_list(db, nidict_list: list[dict]):
    stmt = insert(NewestItem).values(nidict_list)
    db.execute(stmt)
    db.commit()


def insert_urlinitem_dict(db, urlinitem_dict: dict):
    stmt = insert(UrlInItem).values(urlinitem_dict)
    db.execute(stmt)
    db.commit()


def insert_urlinitem_dict_list(db, urlinitem_list: list[dict]):
    stmt = insert(UrlInItem).values(urlinitem_list)
    db.execute(stmt)
    db.commit()


def insert_url(db, url_id: int, urlpath: str):
    stmt = insert(Url).values(
        url_id=url_id,
        urlpath=urlpath,
    )
    db.execute(stmt)
    db.commit()


def insert_url_dict_list(db, url_list: list[dict]):
    stmt = insert(Url).values(url_list)
    db.execute(stmt)
    db.commit()


def insert_stores(db, storename_list: list[str]):
    StoreQuery.add_storename_list(db, storename_list=storename_list)


def insert_store_dict_list(db, storename_dict_list: list[dict]):
    stmt = insert(Store).values(storename_dict_list)
    db.execute(stmt)
    db.commit()


def insert_store_postage_dict_list(db, store_pos_dict_list: list[dict]):
    stmt = insert(StorePostage).values(store_pos_dict_list)
    db.execute(stmt)
    db.commit()


def delete_item_model(db):
    __delete_item_model(db)
    db.commit()


def __delete_item_model(db):
    db.execute(delete(Item))
    db.execute(delete(Url))
    db.execute(delete(UrlInItem))
    db.execute(delete(PriceLog))
    db.execute(delete(PriceLog_2days))
    db.execute(delete(NewestItem))
    db.execute(delete(Group))
    db.execute(delete(GroupItem))


def delete_store_model(db):
    __delete_store_model(db)
    db.commit()


def __delete_store_model(db):
    db.execute(delete(Store))
    db.execute(delete(StorePostage))


def delete_item_and_store_model(db):
    __delete_item_model(db)
    __delete_store_model(db)
    db.commit()


def insert_online_store_dict_list(db, store_dict_list: list[dict]):
    stmt = insert(OnlineStore).values(store_dict_list)
    db.execute(stmt)
    db.commit()


def insert_online_store_postage_dict_list(db, store_pos_dict_list: list[dict]):
    stmt = insert(OnlineStorePostage).values(store_pos_dict_list)
    db.execute(stmt)
    db.commit()


def insert_daily_online_shop_info_dict_list(db, shop_info_dict_list: list[dict]):
    stmt = insert(DailyOnlineShopInfo).values(shop_info_dict_list)
    db.execute(stmt)
    db.commit()


def delete_online_store_model(db):
    db.execute(delete(OnlineStore))
    db.execute(delete(OnlineStorePostage))
    db.execute(delete(Prefecture))
    db.execute(delete(DailyOnlineShopInfo))
    db.commit()

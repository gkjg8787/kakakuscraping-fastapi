from typing import List
from .read_sqlalchemy import getSession

from model.item import (
    PriceLog,
    UrlInItem,
)
from model.store import (
    Store,
    StorePostage,
)
from sqlalchemy import (
    select,
    delete,
)
from accessor.util import (
    utc_to_jst_date_for_query,
    get_jst_date_for_query,
)

class StoreQuery:

    SEL_ALL = select(Store)

    @classmethod
    def get_all(cls):
        ses = getSession()
        return ses.scalars(cls.SEL_ALL).all()
    
    @classmethod
    def add_store(cls, storename :str) -> int:
        ret = cls.get_store_by_storename(storename)
        if ret:
            return ret.store_id
        store = Store(storename=storename)
        ses = getSession()
        ses.add(store)
        ses.commit()
        return store.store_id

    @classmethod
    def add_storename_list(cls, storename_list :List[str]):
        add_list :List[Store] = []
        for storename in storename_list:
            add_list.append(Store(storename=storename))
        ses = getSession()
        ses.add_all(add_list)
        ses.commit()
        ses.close()
    
    @classmethod
    def get_store_by_storename(cls, storename :str) -> Store:
        stmt = ( select(Store)
                .where(Store.storename == storename)
                )
        ses = getSession()
        return ses.scalar(stmt)
    
    @classmethod
    def get_storename_for_calcitemcomb_by_item_id_list(cls, item_id_list :List[int]):
        ses = getSession()
        stmt = ( select(PriceLog.storename)
                    .join(UrlInItem, UrlInItem.url_id == PriceLog.url_id)
                    .where(UrlInItem.active == 'True')
                    .where(UrlInItem.item_id.in_(item_id_list))
                    .where(utc_to_jst_date_for_query(PriceLog.created_at) >= get_jst_date_for_query())
                    .where(PriceLog.issuccess == 1)
                    .where(PriceLog.storename != '')
                    .group_by(PriceLog.storename)
                )
        return ses.execute(stmt).all()
    
    @classmethod
    def insert_storepostage_list(cls, storepostage_list :List):
        ses = getSession()
        ses.add_all(storepostage_list)
        ses.commit()

    @classmethod
    def delete_storepostage_by_store_id_list(cls, store_id_list :List[int]) -> None:
        stmt = ( delete(StorePostage)
                .where(StorePostage.store_id.in_(store_id_list))
                )
        ses = getSession()
        ses.execute(stmt)
        ses.commit()

    @classmethod
    def exist_storename(cls, a, ary) -> bool:
        if not hasattr(a, "storename"):
            return False
        for b in ary:
            if not hasattr(b, "storename"):
                return False
            if a.storename == b.storename:
                return True
        return False

    @classmethod
    def get_unregistered_stores(cls, stores :List[Store]) -> List[Store]:
        names = [s.storename for s in stores]
        ses = getSession()
        stmt = select(Store).where(Store.storename.in_(names))
        exist_stores = ses.scalars(stmt).all()
        not_exist_stores = [s for s in stores if not cls.exist_storename(s, exist_stores)]
        return not_exist_stores
    
    @classmethod
    def regist_stores(cls, storename_list :List[str]):
        stores = []
        for sname in storename_list:
            stores.append(Store(storename=sname))
        not_exist_stores = cls.get_unregistered_stores(stores)
        if len(not_exist_stores) == 0:
            return ()
        with getSession() as ses:
            ses.add_all(not_exist_stores)
            ses.commit()
    
    @classmethod
    def get_storepostage_by_storename(cls, storenames :List[str]):
        ses = getSession()
        j = ( select(Store.store_id,
                   Store.storename,
                   StorePostage.terms_id,
                   StorePostage.boundary,
                   StorePostage.postage,
                   StorePostage.created_at)
                .join(StorePostage, Store.store_id == StorePostage.store_id, isouter=True)
                .subquery()
            )
        stmt = select(j).where(j.c.storename.in_(storenames))
        return ses.execute(stmt).all()
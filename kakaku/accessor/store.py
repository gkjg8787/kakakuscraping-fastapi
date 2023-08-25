from typing import List
from sqlalchemy.orm import Session

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
    def get_all(cls, db :Session):
        return db.scalars(cls.SEL_ALL).all()
    
    @classmethod
    def add_store(cls, db :Session, storename :str) -> int:
        ret = cls.get_store_by_storename(storename)
        if ret:
            return ret.store_id
        store = Store(storename=storename)
        db.add(store)
        db.commit()
        db.refresh(store)
        return store.store_id

    @classmethod
    def add_storename_list(cls, db :Session, storename_list :List[str]):
        add_list :List[Store] = []
        for storename in storename_list:
            add_list.append(Store(storename=storename))
        db.add_all(add_list)
        db.commit()
        for store in add_list:
            db.refresh(store)
    
    @classmethod
    def get_store_by_storename(cls, db :Session, storename :str) -> Store:
        stmt = ( select(Store)
                .where(Store.storename == storename)
                )
        return db.scalar(stmt)
    
    @classmethod
    def get_storename_for_calcitemcomb_by_item_id_list(cls, db :Session, item_id_list :List[int]):
        stmt = ( select(PriceLog.storename)
                    .join(UrlInItem, UrlInItem.url_id == PriceLog.url_id)
                    .where(UrlInItem.active == 'True')
                    .where(UrlInItem.item_id.in_(item_id_list))
                    .where(utc_to_jst_date_for_query(PriceLog.created_at) >= get_jst_date_for_query())
                    .where(PriceLog.issuccess == 1)
                    .where(PriceLog.storename != '')
                    .group_by(PriceLog.storename)
                )
        return db.execute(stmt).all()
    
    @classmethod
    def insert_storepostage_list(cls, db :Session, storepostage_list :List):
        db.add_all(storepostage_list)
        db.commit()
        for storepos in storepostage_list:
            db.refresh(storepos)

    @classmethod
    def delete_storepostage_by_store_id_list(cls, db :Session, store_id_list :List[int]) -> None:
        stmt = ( delete(StorePostage)
                .where(StorePostage.store_id.in_(store_id_list))
                )
        db.execute(stmt)
        db.commit()

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
    def get_unregistered_stores(cls, db :Session, stores :List[Store]) -> List[Store]:
        names = [s.storename for s in stores]
        stmt = select(Store).where(Store.storename.in_(names))
        exist_stores = db.scalars(stmt).all()
        not_exist_stores = [s for s in stores if not cls.exist_storename(s, exist_stores)]
        return not_exist_stores
    
    @classmethod
    def regist_stores(cls, db :Session, storename_list :List[str]):
        stores = []
        for sname in storename_list:
            stores.append(Store(storename=sname))
        not_exist_stores = cls.get_unregistered_stores(db, stores=stores)
        if len(not_exist_stores) == 0:
            return ()

        db.add_all(not_exist_stores)
        db.commit()
        for store in not_exist_stores:
            db.refresh(store)
    
    @classmethod
    def get_storepostage_by_storename(cls, db :Session, storenames :List[str]):
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
        return db.execute(stmt).all()
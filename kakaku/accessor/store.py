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
    update,
)
from accessor.util import (
    utc_to_jst_date_for_query,
    utc_to_jst_datetime_for_query,    
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
    def delete_store_by_store_id(cls, db :Session, store_id :int) -> None:
        stmt = ( delete(Store)
                .where(Store.store_id == store_id)
                )
        db.execute(stmt)
        db.commit()
    
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
    def delete_storepostage_by_list(cls, db :Session, delete_list :list[StorePostage]) -> None:
        base = ( delete(StorePostage)
                )
        for sps in delete_list:
            stmt = (base
                    .where(sps.store_id == StorePostage.store_id)
                    .where(sps.terms_id == StorePostage.terms_id)
                    )
            db.execute(stmt)
        db.commit()
    
    @classmethod
    def update_storepostage_by_list(cls, db :Session, update_list :list[StorePostage]) -> None:
        base = ( update(StorePostage)
                )
        for sps in update_list:
            stmt = (base
                    .where(sps.store_id == StorePostage.store_id)
                    .where(sps.terms_id == StorePostage.terms_id)
                    .values(boundary=sps.boundary,
                            postage=sps.postage
                            )
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
                   utc_to_jst_datetime_for_query(StorePostage.created_at).label("created_at"))
                .join(StorePostage,
                      Store.store_id == StorePostage.store_id,
                      isouter=True
                      )
                .subquery()
            )
        stmt = select(j).where(j.c.storename.in_(storenames))
        return db.execute(stmt).all()
    
    @classmethod
    def get_store_and_postage_stmt(cls):
        stmt = ( select(Store.store_id,
                   Store.storename,
                   utc_to_jst_datetime_for_query(Store.created_at).label("created_at"),
                   StorePostage.terms_id,
                   StorePostage.boundary,
                   StorePostage.postage,
                   utc_to_jst_datetime_for_query(StorePostage.created_at).label("terms_created_at")
                   )
                .join(StorePostage,
                      Store.store_id == StorePostage.store_id,
                      isouter=True
                      )
            )
        return stmt

    @classmethod
    def get_store_and_postage_all(cls, db :Session):
        stmt = cls.get_store_and_postage_stmt()
        return db.execute(stmt).all()
    
    @classmethod
    def get_store_and_postage_by_item_id(cls, db :Session, item_id :int):
        stmt = cls.get_store_and_postage_stmt()
        stmt = (stmt
                .where(Store.store_id == item_id)
                )
        return db.execute(stmt).all()
    
    @classmethod
    def get_storename_by_store_id(cls, db :Session, store_id :int):
        stmt = (select(Store.storename)
                .where(Store.store_id == store_id)
                )
        return db.scalar(stmt)
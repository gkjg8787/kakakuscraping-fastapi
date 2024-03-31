from typing import List
from sqlalchemy.orm import Session

from model.item import (
    PriceLog,
    PriceLog_2days,
    UrlInItem,
)
from model.store import (
    Store,
    StorePostage,
    OnlineStore,
    OnlineStorePostage,
    Prefecture,
    DailyOnlineShopInfo,
)
from sqlalchemy import (
    select,
    delete,
    update,
    func,
    or_,
)
from accessor.util import (
    utc_to_jst_date_for_query,
    utc_to_jst_datetime_for_query,
    get_jst_date_for_query,
)
from common import filter_name


class StoreQuery:
    @classmethod
    def get_all(cls, db: Session):
        return db.scalars(select(Store)).all()

    @classmethod
    def add_store(cls, db: Session, storename: str) -> int:
        ret = cls.get_store_by_storename(storename)
        if ret:
            return ret.store_id
        store = Store(storename=storename)
        db.add(store)
        db.commit()
        db.refresh(store)
        return store.store_id

    @classmethod
    def add_storename_list(cls, db: Session, storename_list: List[str]):
        add_list: List[Store] = []
        for storename in storename_list:
            add_list.append(Store(storename=storename))
        db.add_all(add_list)
        db.commit()
        for store in add_list:
            db.refresh(store)
        return add_list

    @classmethod
    def delete_store_by_store_id(cls, db: Session, store_id: int) -> None:
        stmt = delete(Store).where(Store.store_id == store_id)
        db.execute(stmt)
        db.commit()

    @classmethod
    def get_store_by_storename(cls, db: Session, storename: str) -> Store:
        stmt = select(Store).where(Store.storename == storename)
        return db.scalar(stmt)

    @classmethod
    def get_storename_for_calcitemcomb_by_item_id_list(
        cls, db: Session, item_id_list: List[int]
    ):
        stmt = (
            select(PriceLog.storename)
            .join(UrlInItem, UrlInItem.url_id == PriceLog.url_id)
            .where(UrlInItem.active == "True")
            .where(UrlInItem.item_id.in_(item_id_list))
            .where(
                utc_to_jst_date_for_query(PriceLog.created_at)
                >= get_jst_date_for_query()
            )
            .where(PriceLog.issuccess == 1)
            .where(PriceLog.storename != "")
            .group_by(PriceLog.storename)
        )
        return db.execute(stmt).all()

    @classmethod
    def insert_storepostage_list(cls, db: Session, storepostage_list: List):
        db.add_all(storepostage_list)
        db.commit()
        for storepos in storepostage_list:
            db.refresh(storepos)

    @classmethod
    def delete_storepostage_by_store_id_list(
        cls, db: Session, store_id_list: List[int]
    ) -> None:
        stmt = delete(StorePostage).where(StorePostage.store_id.in_(store_id_list))
        db.execute(stmt)
        db.commit()

    @classmethod
    def delete_storepostage_by_list(
        cls, db: Session, delete_list: list[StorePostage]
    ) -> None:
        base = delete(StorePostage)
        for sps in delete_list:
            stmt = base.where(sps.store_id == StorePostage.store_id).where(
                sps.terms_id == StorePostage.terms_id
            )
            db.execute(stmt)
        db.commit()

    @classmethod
    def update_storepostage_by_list(
        cls, db: Session, update_list: list[StorePostage]
    ) -> None:
        base = update(StorePostage)
        for sps in update_list:
            stmt = (
                base.where(sps.store_id == StorePostage.store_id)
                .where(sps.terms_id == StorePostage.terms_id)
                .values(boundary=sps.boundary, postage=sps.postage)
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
    def get_unregistered_stores(cls, db: Session, stores: List[Store]) -> List[Store]:
        names = [s.storename for s in stores]
        stmt = select(Store).where(Store.storename.in_(names))
        exist_stores = db.scalars(stmt).all()
        not_exist_stores = [
            s for s in stores if not cls.exist_storename(s, exist_stores)
        ]
        return not_exist_stores

    @classmethod
    def regist_stores(cls, db: Session, storename_list: List[str]):
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
    def get_storepostage_by_storename(
        cls, db: Session, storenames: list[str], fq: dict = {}
    ):
        stmt = (
            select(
                Store.store_id,
                Store.storename,
                StorePostage.terms_id,
                StorePostage.boundary,
                StorePostage.postage,
                utc_to_jst_datetime_for_query(StorePostage.created_at).label(
                    "created_at"
                ),
            )
            .join(StorePostage, Store.store_id == StorePostage.store_id, isouter=True)
            .where(Store.storename.in_(storenames))
        )
        stmt = cls._set_store_list_filter(stmt=stmt, fq=fq)
        return db.execute(stmt).all()

    @classmethod
    def get_store_and_postage_all_utc(cls, db: Session):
        stmt = (
            select(
                Store.store_id,
                Store.storename,
                Store.created_at,
                StorePostage.terms_id,
                StorePostage.boundary,
                StorePostage.postage,
                StorePostage.created_at.label("terms_created_at"),
            )
            .join(StorePostage, Store.store_id == StorePostage.store_id, isouter=True)
            .order_by(Store.store_id, StorePostage.terms_id)
        )
        return db.execute(stmt).all()

    @classmethod
    def get_store_and_postage_local_time_stmt(cls):
        stmt = select(
            Store.store_id,
            Store.storename,
            utc_to_jst_datetime_for_query(Store.created_at).label("created_at"),
            StorePostage.terms_id,
            StorePostage.boundary,
            StorePostage.postage,
            utc_to_jst_datetime_for_query(StorePostage.created_at).label(
                "terms_created_at"
            ),
        ).join(StorePostage, Store.store_id == StorePostage.store_id, isouter=True)
        return stmt

    @classmethod
    def _set_store_list_filter(cls, stmt, fq: dict):
        if filter_name.FilterQueryName.SORT.value in fq:
            sort_id = int(fq[filter_name.FilterQueryName.SORT.value])
        else:
            return stmt
        match sort_id:
            case filter_name.StoreListSortName.NAME_ASC.id:
                return stmt.order_by(Store.storename.asc())
            case filter_name.StoreListSortName.NAME_DESC.id:
                return stmt.order_by(Store.storename.desc())
            case filter_name.StoreListSortName.OLD_STORE.id:
                return stmt.order_by(Store.store_id.asc())
            case filter_name.StoreListSortName.NEW_STORE.id:
                return stmt.order_by(Store.store_id.desc())
            case filter_name.StoreListSortName.SHIPPING_ASC.id:
                return stmt.order_by(StorePostage.postage.asc(), Store.store_id.asc())
            case filter_name.StoreListSortName.SHIPPING_DESC.id:
                return stmt.order_by(StorePostage.postage.desc(), Store.store_id.asc())
            case _:
                return stmt

    @classmethod
    def _set_store_terms_configured_filter(cls, stmt, fq: dict):
        if filter_name.FilterQueryName.CONFED.value not in fq:
            return stmt
        confed_id = int(fq[filter_name.FilterQueryName.CONFED.value])
        match confed_id:
            case filter_name.StoreTermsConfiguredFilterName.ALL.id:
                return stmt
            case filter_name.StoreTermsConfiguredFilterName.CONFIGURED.id:
                return stmt.where(StorePostage.boundary.is_not(None))
            case filter_name.StoreTermsConfiguredFilterName.NONE.id:
                return stmt.where(StorePostage.boundary.is_(None))
            case _:
                return stmt

    @classmethod
    def get_store_and_postage_all(cls, db: Session, fq: dict = {}):
        stmt = cls.get_store_and_postage_local_time_stmt()
        stmt = cls._set_store_terms_configured_filter(stmt=stmt, fq=fq)
        stmt = cls._set_store_list_filter(stmt=stmt, fq=fq)
        return db.execute(stmt).all()

    @classmethod
    def get_store_and_postage_by_item_id(cls, db: Session, item_id: int):
        stmt = cls.get_store_and_postage_local_time_stmt()
        stmt = stmt.where(Store.store_id == item_id)
        return db.execute(stmt).all()

    @classmethod
    def get_storename_by_store_id(cls, db: Session, store_id: int):
        stmt = select(Store.storename).where(Store.store_id == store_id)
        return db.scalar(stmt)

    @classmethod
    def delete_store_by_not_in_storenames(cls, db: Session, storename_list: list[str]):
        store_ids_q = select(Store.store_id).where(
            Store.storename.not_in(storename_list)
        )
        delete_store = delete(Store).where(Store.store_id.in_(store_ids_q))
        db.execute(delete_store)
        db.commit()

    @classmethod
    def delete_all_storepostage(cls, db: Session):
        stmt = delete(StorePostage)
        db.execute(stmt)
        db.commit()

    @classmethod
    def add_postage_by_add_postage_dict(
        cls, db: Session, add_postage_dict: dict[str, list[StorePostage]]
    ):
        add_list: list[StorePostage] = []
        for st_list in add_postage_dict.values():
            db.add_all(st_list)
            add_list.extend(st_list)
        db.commit()
        for a in add_list:
            db.refresh(a)


class OnlineStoreQuery:
    @classmethod
    def get_all_stmt(cls):
        return (
            select(
                OnlineStore.shop_id,
                OnlineStore.storename,
                OnlineStore.created_at,
                OnlineStorePostage.pref_id,
                OnlineStorePostage.terms_id,
                OnlineStorePostage.boundary,
                OnlineStorePostage.postage,
                OnlineStorePostage.campaign_msg,
                OnlineStorePostage.insert_proc_type,
                OnlineStorePostage.created_at.label("terms_created_at"),
            )
            .select_from(OnlineStore)
            .join(
                OnlineStorePostage,
                OnlineStore.shop_id == OnlineStorePostage.shop_id,
                isouter=True,
            )
        )

    @classmethod
    def get_all(cls, db: Session):
        stmt = cls.get_all_stmt().order_by(
            OnlineStore.shop_id.asc(),
            OnlineStorePostage.pref_id,
            OnlineStorePostage.terms_id,
        )
        return db.execute(stmt).all()

    @classmethod
    def get_all_by_prefname(cls, db: Session, pref_name_list: list[str]):
        stmt = (
            cls.get_all_stmt()
            .join(Prefecture, Prefecture.pref_id == OnlineStorePostage.pref_id)
            .where(Prefecture.name.in_(pref_name_list))
            .order_by(
                OnlineStore.shop_id.asc(),
                OnlineStorePostage.pref_id,
                OnlineStorePostage.terms_id,
            )
        )
        return db.execute(stmt).all()

    @classmethod
    def get_all_local_time_stmt(cls):
        return (
            select(
                OnlineStore.shop_id,
                OnlineStore.storename,
                utc_to_jst_datetime_for_query(OnlineStore.created_at).label(
                    "created_at"
                ),
                OnlineStorePostage.pref_id,
                OnlineStorePostage.terms_id,
                OnlineStorePostage.boundary,
                OnlineStorePostage.postage,
                OnlineStorePostage.campaign_msg,
                OnlineStorePostage.insert_proc_type,
                utc_to_jst_datetime_for_query(OnlineStorePostage.created_at).label(
                    "terms_created_at"
                ),
                DailyOnlineShopInfo.shop_id.label("tenpo_code"),
            )
            .select_from(OnlineStore)
            .join(
                OnlineStorePostage,
                OnlineStore.shop_id == OnlineStorePostage.shop_id,
                isouter=True,
            )
            .join(
                DailyOnlineShopInfo,
                OnlineStore.storename == DailyOnlineShopInfo.shop_name,
                isouter=True,
            )
        )

    @classmethod
    def set_store_sort_filter(cls, stmt, fq: dict):
        if filter_name.FilterQueryName.SORT.value in fq:
            sort_id = int(fq[filter_name.FilterQueryName.SORT.value])
        else:
            return stmt.order_by(
                OnlineStore.shop_id.asc(),
                OnlineStorePostage.pref_id,
                OnlineStorePostage.terms_id,
            )
        match sort_id:
            case filter_name.StoreListSortName.NAME_ASC.id:
                return stmt.order_by(
                    OnlineStore.storename.asc(),
                    OnlineStore.shop_id.asc(),
                    OnlineStorePostage.pref_id.asc(),
                    OnlineStorePostage.terms_id.asc(),
                )
            case filter_name.StoreListSortName.NAME_DESC.id:
                return stmt.order_by(
                    OnlineStore.storename.desc(),
                    OnlineStore.shop_id.asc(),
                    OnlineStorePostage.pref_id.asc(),
                    OnlineStorePostage.terms_id.asc(),
                )
            case filter_name.StoreListSortName.OLD_STORE.id:
                return stmt.order_by(
                    OnlineStore.shop_id.asc(),
                    OnlineStorePostage.pref_id.asc(),
                    OnlineStorePostage.terms_id.asc(),
                )
            case filter_name.StoreListSortName.NEW_STORE.id:
                return stmt.order_by(
                    OnlineStore.shop_id.desc(),
                    OnlineStorePostage.pref_id.asc(),
                    OnlineStorePostage.terms_id.asc(),
                )
            case _:
                return stmt

    @classmethod
    def set_store_terms_configured_filter(cls, stmt, fq: dict):
        if filter_name.FilterQueryName.CONFED.value not in fq:
            return stmt
        confed_id = int(fq[filter_name.FilterQueryName.CONFED.value])
        match confed_id:
            case filter_name.StoreTermsConfiguredFilterName.ALL.id:
                return stmt
            case filter_name.StoreTermsConfiguredFilterName.CONFIGURED.id:
                return stmt.where(OnlineStorePostage.boundary.is_not(None))
            case filter_name.StoreTermsConfiguredFilterName.NONE.id:
                return stmt.where(OnlineStorePostage.boundary.is_(None))
            case _:
                return stmt

    @classmethod
    def set_pref_filter(cls, stmt, fq: dict):
        if filter_name.FilterQueryName.PREF.value not in fq:
            return stmt
        return stmt.join(
            Prefecture, OnlineStorePostage.pref_id == Prefecture.pref_id, isouter=True
        ).where(Prefecture.name == fq[filter_name.FilterQueryName.PREF.value])

    @classmethod
    def set_shop_id_filter(cls, stmt, fq: dict):
        if filter_name.FilterQueryName.STORE.value not in fq:
            return stmt
        return stmt.where(
            OnlineStore.shop_id == int(fq[filter_name.FilterQueryName.STORE.value])
        )

    @classmethod
    def get_all_local_time_by_query(cls, db: Session, fq: dict):
        stmt = cls.get_all_local_time_stmt()
        stmt = cls.set_shop_id_filter(stmt, fq)
        stmt = cls.set_store_terms_configured_filter(stmt, fq)
        stmt = cls.set_pref_filter(stmt, fq)
        stmt = cls.set_store_sort_filter(stmt, fq)
        return db.execute(stmt).all()

    @classmethod
    def get_storename_list(cls, db: Session) -> list[str] | None:
        stmt = select(OnlineStore.storename)
        return db.scalars(stmt).all()

    @classmethod
    def get_onlinestore_all_sorted_by_storename(
        cls, db: Session
    ) -> list[OnlineStore] | None:
        stmt = select(OnlineStore).order_by(OnlineStore.storename)
        return db.scalars(stmt).all()

    @classmethod
    def get_postage_including_none_by_storename_list(
        cls,
        db: Session,
        storename_list: list[str],
        insert_proc_type_list: list[int] = [],
    ):
        stmt = (
            select(
                OnlineStore.shop_id,
                OnlineStore.storename,
                OnlineStorePostage.pref_id,
                OnlineStorePostage.terms_id,
                OnlineStorePostage.boundary,
                OnlineStorePostage.postage,
                OnlineStorePostage.campaign_msg,
                OnlineStorePostage.insert_proc_type,
                OnlineStorePostage.created_at.label("created_at"),
            )
            .select_from(OnlineStore)
            .join(
                OnlineStorePostage,
                OnlineStore.shop_id == OnlineStorePostage.shop_id,
                isouter=True,
            )
            .where(OnlineStore.storename.in_(storename_list))
            .order_by(
                OnlineStore.shop_id.asc(),
                OnlineStorePostage.pref_id,
                OnlineStorePostage.terms_id,
            )
        )
        if insert_proc_type_list:
            stmt = stmt.where(
                or_(
                    OnlineStorePostage.insert_proc_type.in_(insert_proc_type_list),
                    OnlineStorePostage.insert_proc_type.is_(None),
                )
            )
        return db.execute(stmt).all()

    @classmethod
    def get_count_postage_not_updated_today(
        cls, db: Session, insert_proc_type_list: list[int] = []
    ):
        stmt = (
            select(func.count(OnlineStore.shop_id))
            .join(
                OnlineStorePostage,
                OnlineStore.shop_id == OnlineStorePostage.shop_id,
                isouter=True,
            )
            .where(
                or_(
                    OnlineStorePostage.created_at.is_(None),
                    utc_to_jst_date_for_query(OnlineStorePostage.created_at)
                    < get_jst_date_for_query(),
                )
            )
        )
        if insert_proc_type_list:
            stmt = stmt.where(
                or_(
                    OnlineStorePostage.insert_proc_type.in_(insert_proc_type_list),
                    OnlineStorePostage.insert_proc_type.is_(None),
                )
            )
        return db.scalar(stmt)

    @classmethod
    def get_shop_id(cls, db: Session, storename: str) -> int | None:
        stmt = select(OnlineStore.shop_id).where(OnlineStore.storename == storename)
        return db.scalar(stmt)

    @classmethod
    def add_store(cls, db: Session, storename: str) -> int:
        os = OnlineStore(storename=storename)
        db.add(os)
        db.commit()
        db.refresh(os)
        return os.shop_id

    @classmethod
    def add_postage_by_dict_list(
        cls,
        db: Session,
        shop_id: int,
        start_terms_id: int,
        pos_dict_list: list[dict],
    ):
        osp_list: list[OnlineStorePostage] = []
        pref_id_to_terms_id: dict[int, int] = {}
        for dic in pos_dict_list:
            if int(dic["pref_id"]) in pref_id_to_terms_id:
                terms_id = pref_id_to_terms_id[int(dic["pref_id"])] + 1
            else:
                terms_id = start_terms_id
            pref_id_to_terms_id[int(dic["pref_id"])] = terms_id

            osp = OnlineStorePostage(
                shop_id=shop_id,
                pref_id=dic["pref_id"],
                terms_id=terms_id,
                boundary=dic["boundary"],
                postage=dic["postage"],
                campaign_msg=dic["campaign_msg"],
                insert_proc_type=dic["insert_proc_type"],
            )
            osp_list.append(osp)
            db.add(osp)

        if not osp_list:
            return
        db.commit()
        for osp in osp_list:
            db.refresh(osp)

    @classmethod
    def delete_store_by_not_in_storename_list(
        cls,
        db: Session,
        storename_list: list[str],
    ):
        stmt = delete(OnlineStore).where(OnlineStore.storename.not_in(storename_list))
        db.execute(stmt)
        db.commit()

    @classmethod
    def delete_postage_by_storename_and_pref_id(
        cls,
        db: Session,
        storename: str,
        pref_id: int,
        insert_proc_type_list: list[int] = [],
    ):
        shop_id_q = (
            select(OnlineStore.shop_id).where(OnlineStore.storename == storename)
        ).scalar_subquery()
        stmt = (
            delete(OnlineStorePostage)
            .where(OnlineStorePostage.shop_id == shop_id_q)
            .where(OnlineStorePostage.pref_id == pref_id)
        )
        if insert_proc_type_list:
            stmt = stmt.where(
                OnlineStorePostage.insert_proc_type.in_(insert_proc_type_list)
            )
        db.execute(stmt)
        db.commit()

    @classmethod
    def delete_postage(
        cls,
        db: Session,
        insert_proc_type_list: list[int] = [],
        delete_older_than_today: bool = False,
    ):
        stmt = delete(OnlineStorePostage)
        if insert_proc_type_list:
            stmt = stmt.where(
                OnlineStorePostage.insert_proc_type.in_(insert_proc_type_list)
            )
        if delete_older_than_today:
            stmt = stmt.where(
                utc_to_jst_date_for_query(OnlineStorePostage.created_at)
                < get_jst_date_for_query()
            )
        db.execute(stmt)
        db.commit()

    @classmethod
    def delete_postage_by_not_in_storename_list(
        cls, db: Session, storename_list: list[str]
    ):
        shop_ids_q = select(OnlineStore.shop_id).where(
            OnlineStore.storename.in_(storename_list)
        )
        stmt = delete(OnlineStorePostage).where(
            OnlineStorePostage.shop_id.not_in(shop_ids_q)
        )
        db.execute(stmt)
        db.commit()

    @classmethod
    def delete_postage_by_shop_id_and_insert_proc_type(
        cls, db: Session, shop_id: int, insert_proc_type: int
    ):
        stmt = (
            delete(OnlineStorePostage)
            .where(OnlineStorePostage.shop_id == shop_id)
            .where(OnlineStorePostage.insert_proc_type == insert_proc_type)
        )
        db.execute(stmt)
        db.commit()

    @classmethod
    def delete_postage_by_shop_id_and_pref_id_list_and_insert_proc_type(
        cls, db: Session, shop_id: int, pref_id_list: list[int], insert_proc_type: int
    ):
        stmt = (
            delete(OnlineStorePostage)
            .where(OnlineStorePostage.shop_id == shop_id)
            .where(OnlineStorePostage.pref_id.in_(pref_id_list))
            .where(OnlineStorePostage.insert_proc_type == insert_proc_type)
        )
        db.execute(stmt)
        db.commit()

    @classmethod
    def update_postage_by_dict_list(
        cls, db: Session, shop_id: int, pos_dict_list: list[dict]
    ):
        for pos_dict in pos_dict_list:
            stmt = (
                update(OnlineStorePostage)
                .where(OnlineStorePostage.shop_id == shop_id)
                .where(OnlineStorePostage.pref_id == pos_dict["pref_id"])
                .where(OnlineStorePostage.terms_id == pos_dict["terms_id"])
                .where(
                    OnlineStorePostage.insert_proc_type == pos_dict["insert_proc_type"]
                )
                .values(
                    {
                        "boundary": pos_dict["boundary"],
                        "postage": pos_dict["postage"],
                        "created_at": pos_dict["created_at"],
                    }
                )
            )
            db.execute(stmt)
        db.commit()

    @classmethod
    def get_todays_storenames(cls, db: Session):
        stmt = select(PriceLog_2days.storename.distinct()).where(
            utc_to_jst_date_for_query(PriceLog_2days.created_at)
            == get_jst_date_for_query()
        )
        return db.scalars(stmt).all()


class PrefectureQuery:
    @classmethod
    def add_all(cls, db: Session, pref_list: list[Prefecture]):
        for pref in pref_list:
            db.add(pref)
        if not pref_list:
            return
        db.commit()

    @classmethod
    def get_by_prefname_list(cls, db: Session, prefname_list: list[str]):
        stmt = select(Prefecture).where(Prefecture.name.in_(prefname_list))
        return db.scalars(stmt).all()

    @classmethod
    def get_all(cls, db: Session) -> list[Prefecture] | None:
        stmt = select(Prefecture)
        return db.scalars(stmt).all()


class DailyOnlineShopInfoQuery:
    @classmethod
    def get_all(cls, db: Session) -> list[DailyOnlineShopInfo] | None:
        stmt = select(DailyOnlineShopInfo)
        return db.scalars(stmt).all()

    @classmethod
    def get_by_contains_storename(cls, db: Session, storename: str):
        stmt = select(DailyOnlineShopInfo).where(
            DailyOnlineShopInfo.shop_name.contains(storename)
        )
        return db.scalars(stmt).all()

    @classmethod
    def get_shop_id_by_storename(cls, db: Session, storename: str):
        stmt = select(DailyOnlineShopInfo.shop_id).where(
            DailyOnlineShopInfo.shop_name == storename
        )
        return db.scalar(stmt)

    @classmethod
    def add_all(cls, db: Session, add_list: list[DailyOnlineShopInfo]):
        db.add_all(add_list)
        db.commit()
        for a in add_list:
            db.refresh(a)

    @classmethod
    def delete(
        cls,
        db: Session,
        insert_proc_type_list: list[int] = [],
        delete_older_than_today: bool = False,
    ):
        stmt = delete(DailyOnlineShopInfo)
        if insert_proc_type_list:
            stmt = stmt.where(
                DailyOnlineShopInfo.insert_proc_type.in_(insert_proc_type_list)
            )
        if delete_older_than_today:
            stmt = stmt.where(
                utc_to_jst_date_for_query(DailyOnlineShopInfo.created_at)
                < get_jst_date_for_query()
            )
        db.execute(stmt)
        db.commit()

    @classmethod
    def get_todays_count(cls, db: Session, insert_proc_type_list: list[int] = []):
        stmt = select(func.count(DailyOnlineShopInfo.shop_id)).where(
            utc_to_jst_date_for_query(DailyOnlineShopInfo.created_at)
            == get_jst_date_for_query()
        )
        if insert_proc_type_list:
            stmt = stmt.where(
                DailyOnlineShopInfo.insert_proc_type.in_(insert_proc_type_list)
            )
        return db.scalar(stmt)

    @classmethod
    def get_count_before_today(cls, db: Session, insert_proc_type_list: list[int] = []):
        stmt = select(func.count(DailyOnlineShopInfo.shop_id)).where(
            utc_to_jst_date_for_query(DailyOnlineShopInfo.created_at)
            < get_jst_date_for_query()
        )
        if insert_proc_type_list:
            stmt = stmt.where(
                DailyOnlineShopInfo.insert_proc_type.in_(insert_proc_type_list)
            )
        return db.scalar(stmt)

    @classmethod
    def update(cls, db: Session, update_list: list[DailyOnlineShopInfo]):
        if not update_list:
            return
        for dosi in update_list:
            dic = dosi.toDict()
            shop_id = dic.pop("shop_id")
            stmt = (
                update(DailyOnlineShopInfo)
                .where(DailyOnlineShopInfo.shop_id == shop_id)
                .values(dic)
            )
            db.execute(stmt)
        db.commit()

from enum import Enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    select,
    insert,
    delete,
    update,
    union,
    func,
    between,
    and_,
    or_,
)

from sqlalchemy.sql import expression as exp
from sqlalchemy.orm import Session

from common import const_value, util
from common.filter_name import (
    FilterQueryName as fqn,
    ActFilterName,
    ItemSortName,
    ItemPurchaseSortName,
    UrlSortName,
    ExtractStoreSortName,
    FilterOnOff,
)
from model.item import (
    Item,
    Url,
    UrlInItem,
    NewestItem,
    Group,
    GroupItem,
    PriceLog,
    PriceLog_2days,
)
from model.store import (
    Store,
)

from accessor.util import (
    utc_to_jst_datetime_for_query,
    utc_to_jst_date_for_query,
    get_jst_datetime_for_query,
    get_jst_date_for_query,
    INTERVAL_ONE_YEARS_AGO,
    INTERVAL_YESTERDAY,
    text_to_boolean,
    text_to_decimal,
)

from html_parser.htmlparse import ParseItemInfo

# from common.stop_watch import stop_watch


class UrlActive(Enum):
    ACTIVE = "True"
    INACTIVE = "False"


def get_act_filter(filter: dict) -> UrlActive | None:
    if (
        fqn.ACT.value not in filter.keys()
        or int(filter[fqn.ACT.value]) == ActFilterName.ALL.id
    ):
        return None
    if int(filter[fqn.ACT.value]) == ActFilterName.ACT.id:
        return UrlActive.ACTIVE
    if int(filter[fqn.ACT.value]) == ActFilterName.INACT.id:
        return UrlActive.INACTIVE
    return None


class NewestQuery:
    act_t = (
        select(UrlInItem.item_id, func.count(UrlInItem.url_id).label("act"))
        .where(UrlInItem.active == UrlActive.ACTIVE.value)
        .group_by(UrlInItem.item_id)
        .cte("act_t")
    )
    inact_t = (
        select(Item.item_id, exp.literal(0).label("act"))
        .where(Item.item_id.notin_(select(act_t.c.item_id)))
        .group_by(Item.item_id)
        .cte("inact_t")
    )
    actcheck = select(act_t).union(inact_t.select()).cte("actcheck")
    base_select = (
        select(
            Item.item_id,
            Item.name,
            Url.url_id,
            Url.urlpath,
            utc_to_jst_datetime_for_query(NewestItem.created_at).label("created_at"),
            NewestItem.newestprice.label("price"),
            NewestItem.salename,
            NewestItem.trendrate,
            NewestItem.storename,
            NewestItem.lowestprice,
            actcheck.c.act,
        )
        .join(NewestItem, Item.item_id == NewestItem.item_id, isouter=True)
        .join(Url, NewestItem.url_id == Url.url_id, isouter=True)
        .join(actcheck, actcheck.c.item_id == Item.item_id, isouter=True)
    )

    @classmethod
    def get_base_select(cls):
        return cls.base_select

    @classmethod
    def get_newest_data(cls, db: Session, filter: dict):
        stmt = cls.get_newest_filter_statement(filter)
        return db.execute(stmt).all()

    @classmethod
    def get_newest_data_for_edit_group(
        cls, db: Session, filter: dict, ignore_group_id: int
    ):
        stmt = cls.get_base_select()
        stmt = cls.__set_not_include_group_filter(
            filter={fqn.GID.value: ignore_group_id}, stmt=stmt
        )
        stmt = cls.__set_act_filter(filter, stmt)
        stmt = cls.__set_in_stock_filter(filter, stmt)
        stmt = cls.__set_eq_storename(filter, stmt)
        stmt = cls.__set_price_range_filter(filter, stmt)
        stmt = cls.__set_itemsort_filter(filter, stmt)
        return db.execute(stmt).all()

    @classmethod
    def get_newest_data_of_group(cls, db: Session, group_id: int):
        stmt = cls.get_base_select()
        stmt = cls.__set_group_filter(filter={fqn.GID.value: group_id}, stmt=stmt)
        stmt = stmt.order_by(Item.item_id.asc())
        return db.execute(stmt).all()

    @classmethod
    def get_newest_data_by_item_id(cls, db: Session, item_id: int):
        stmt = cls.get_base_select().where(Item.item_id == item_id)
        return db.execute(stmt).one_or_none()

    @classmethod
    def get_newest_filter_statement(cls, filter: dict):
        stmt = cls.get_base_select()
        stmt = cls.__set_group_filter(filter, stmt)
        stmt = cls.__set_act_filter(filter, stmt)
        stmt = cls.__set_in_stock_filter(filter, stmt)
        stmt = cls.__set_eq_storename(filter, stmt)
        stmt = cls.__set_price_range_filter(filter, stmt)
        stmt = cls.__set_itemsort_filter(filter, stmt)
        return stmt

    @classmethod
    def __set_act_filter(cls, filter: dict, stmt):
        if (
            fqn.ACT.value not in filter.keys()
            or int(filter[fqn.ACT.value]) == ActFilterName.ALL.id
        ):
            return stmt
        if int(filter[fqn.ACT.value]) == ActFilterName.ACT.id:
            return stmt.where(cls.actcheck.c.act > 0)
        if int(filter[fqn.ACT.value]) == ActFilterName.INACT.id:
            return stmt.where(cls.actcheck.c.act == 0)
        return stmt

    @classmethod
    def __set_in_stock_filter(cls, filter: dict, stmt):
        if (
            fqn.ZAIKO.value not in filter.keys()
            or int(filter[fqn.ZAIKO.value]) != FilterOnOff.ON
        ):
            return stmt
        return stmt.where(NewestItem.newestprice > const_value.INIT_PRICE)

    @classmethod
    def __set_group_filter(cls, filter: dict, stmt):
        if fqn.GID.value not in filter.keys() or int(filter[fqn.GID.value]) < 0:
            return stmt
        stmt = stmt.join(GroupItem, GroupItem.item_id == Item.item_id).where(
            GroupItem.group_id == int(filter[fqn.GID.value])
        )
        return stmt

    @classmethod
    def __set_not_include_group_filter(cls, filter: dict, stmt):
        if fqn.GID.value not in filter.keys() or int(filter[fqn.GID.value]) < 0:
            return stmt
        stmt = stmt.where(
            Item.item_id.not_in(
                select(GroupItem.item_id).where(
                    GroupItem.group_id == int(filter[fqn.GID.value])
                )
            )
        )
        return stmt

    @classmethod
    def __set_itemsort_filter(cls, filter: dict, stmt):
        if fqn.ISORT.value not in filter.keys() or int(filter[fqn.ISORT.value]) < 0:
            stmt = stmt.order_by(Item.item_id.asc())
            return stmt
        fnum = int(filter[fqn.ISORT.value])
        if fnum == ItemSortName.OLD_ITEM.id:
            stmt = stmt.order_by(Item.item_id.asc())
            return stmt
        if fnum == ItemSortName.NEW_ITEM.id:
            stmt = stmt.order_by(Item.item_id.desc())
            return stmt
        if fnum == ItemSortName.LOW_PRICE.id:
            stmt = stmt.order_by(NewestItem.newestprice.label("price").asc())
            return stmt
        if fnum == ItemSortName.HIGH_PRICE.id:
            stmt = stmt.order_by(NewestItem.newestprice.label("price").desc())
            return stmt
        if fnum == ItemSortName.ITEM_NAME.id:
            stmt = stmt.order_by(Item.name.asc())
            return stmt
        if fnum == ItemSortName.STORE_NAME.id:
            stmt = stmt.order_by(NewestItem.storename.asc())
            return stmt
        if fnum == ItemSortName.LOW_TRENDRATE.id:
            stmt = stmt.order_by(text_to_decimal(NewestItem.trendrate).asc())
            return stmt
        if fnum == ItemSortName.HIGH_TRENDRATE.id:
            stmt = stmt.order_by(text_to_decimal(NewestItem.trendrate).desc())
            return stmt
        if fnum == ItemSortName.OLD_UPDATE_TIME.id:
            stmt = stmt.order_by(NewestItem.created_at.asc())
            return stmt
        if fnum == ItemSortName.NEW_UPDATE_TIME.id:
            stmt = stmt.order_by(NewestItem.created_at.desc())
            return stmt
        if fnum == ItemSortName.LOW_LOWESTPRICE.id:
            stmt = stmt.order_by(NewestItem.lowestprice.asc())
            return stmt
        if fnum == ItemSortName.HIGH_LOWESTPRICE.id:
            stmt = stmt.order_by(NewestItem.lowestprice.desc())
            return stmt
        if (
            fnum == ItemSortName.CLOSEST_LOWESTPRICE.id
            or fnum == ItemSortName.FURTHEST_LOWESTPRICE.id
        ):
            diff_t = cls.get_diff_query_between_newestprice_and_lowestprice().cte(
                "diff_t"
            )
            if fnum == ItemSortName.CLOSEST_LOWESTPRICE.id:
                stmt = stmt.join(
                    diff_t, diff_t.c.item_id == NewestItem.item_id
                ).order_by(diff_t.c.diff.asc(), NewestItem.item_id.asc())
            else:
                stmt = stmt.join(
                    diff_t, diff_t.c.item_id == NewestItem.item_id
                ).order_by(diff_t.c.diff.desc(), NewestItem.item_id.asc())
            return stmt
        return stmt

    @classmethod
    def get_diff_query_between_newestprice_and_lowestprice(cls):
        stmt = select(
            NewestItem.item_id,
            (NewestItem.newestprice - NewestItem.lowestprice).label("diff"),
        ).where(NewestItem.newestprice > const_value.INIT_PRICE)
        return stmt

    @classmethod
    def __set_eq_storename(cls, filter: dict, stmt):
        if fqn.STORE.value not in filter.keys() or int(filter[fqn.STORE.value]) < 0:
            return stmt
        stmt = stmt.join(Store, Store.storename == NewestItem.storename).where(
            Store.store_id == int(filter[fqn.STORE.value])
        )
        return stmt

    @classmethod
    def __set_price_range_filter(cls, filter: dict, stmt):
        if fqn.PRMIN.value in filter.keys() and fqn.PRMAX.value in filter.keys():
            min = int(filter[fqn.PRMIN.value])
            max = int(filter[fqn.PRMAX.value])
            if min == max:
                stmt = stmt.where(NewestItem.newestprice == min)
                return stmt
            if min > max:
                return stmt
            stmt = stmt.where(NewestItem.newestprice >= min).where(
                NewestItem.newestprice <= max
            )
            return stmt
        if fqn.PRMIN.value in filter.keys():
            stmt = stmt.where(NewestItem.newestprice >= int(filter[fqn.PRMIN.value]))
            return stmt
        if fqn.PRMAX.value in filter.keys():
            stmt = stmt.where(NewestItem.newestprice <= int(filter[fqn.PRMAX.value]))
            return stmt
        return stmt

    @classmethod
    def add_item(cls, item_name: str, url_path: str, db: Session):
        if url_path:
            url_id = UrlQuery.add_url(db=db, urlpath=url_path)
            if url_id >= 0:
                if item_name:
                    item_id = ItemQuery.add(db=db, name=item_name)
                else:
                    item_id = ItemQuery.add(db)
                UrlQuery.add_urlinitem(db, url_id=url_id, item_id=item_id)
                cls.__add_newest_data(db, item_id=item_id)
                return
        elif item_name:
            item_id = ItemQuery.add(db=db, name=item_name)
            cls.__add_newest_data(db, item_id=item_id)
        return

    @classmethod
    def __add_newest_data(cls, db: Session, item_id: int):
        ni = NewestItem(
            item_id=item_id,
            newestprice=const_value.INIT_PRICE,
            lowestprice=const_value.INIT_PRICE,
        )
        db.add(ni)
        db.commit()
        db.refresh(ni)

    @classmethod
    def update_items_by_dict(cls, db: Session, nidict: dict) -> None:
        if "url_id" not in nidict:
            return
        itemids = cls.__get_item_id_from_urlinitem_by_url_id(
            db, url_id=int(nidict["url_id"])
        )
        if not itemids or len(itemids) == 0:
            return
        for itemid in itemids:
            ni = db.get(NewestItem, itemid)
            if cls.__is_update_item(ni, nidict):
                pi = ParseItemInfo()
                pi.usedPrice = nidict["newestprice"]
                pi.oldPrice = ItemQuery.get_most_recent_old_price_of_2days_by_item_id(
                    db, item_id=itemid
                )
                if not pi.oldPrice:
                    pi.oldPrice = const_value.INIT_PRICE
                nidict["trendrate"] = pi.getTrendRate()
                nidict["lowestprice"] = cls.__get_lowest_price_ever(
                    db, item_id=itemid, newestprice=nidict["newestprice"]
                )
                stmt = (
                    update(NewestItem)
                    .where(NewestItem.item_id == itemid)
                    .values(nidict)
                )
                db.execute(stmt)
        db.commit()

    @classmethod
    def __get_lowest_price_ever(cls, db: Session, item_id: int, newestprice: int):
        price = NewestQuery.get_lowest_price_ever(db, item_id=item_id)
        if price == const_value.INIT_PRICE:
            return newestprice
        if newestprice == const_value.INIT_PRICE:
            return price
        if price > newestprice:
            return newestprice
        return price

    @staticmethod
    def __is_update_item(ni: NewestItem, nidict: dict) -> bool:
        if (
            not util.isLocalToday(util.utcTolocaltime(ni.created_at))
            or (
                ni.newestprice == const_value.INIT_PRICE
                and int(nidict["newestprice"] != const_value.INIT_PRICE)
            )
            or (
                ni.newestprice > int(nidict["newestprice"])
                and int(nidict["newestprice"] != const_value.INIT_PRICE)
            )
        ):
            return True
        return False

    @classmethod
    def get_item_id_from_urlinitem_by_url_id(cls, db: Session, url_id: int):
        return cls.__get_item_id_from_urlinitem_by_url_id(db, url_id=url_id)

    @classmethod
    def __get_item_id_from_urlinitem_by_url_id(cls, db: Session, url_id: int):
        stmt = (
            select(UrlInItem.item_id)
            .where(UrlInItem.url_id == url_id)
            .group_by(UrlInItem.item_id)
        )
        return db.scalars(stmt).all()

    @classmethod
    def get_lowest_price_ever(cls, db: Session, item_id: int):
        stmt = select(NewestItem.lowestprice).where(NewestItem.item_id == item_id)
        return db.scalar(stmt)

    @classmethod
    def get_storenames(cls, db: Session) -> list:
        stmt = select(NewestItem.storename).group_by(NewestItem.storename)
        return db.execute(stmt).all()

    @classmethod
    def get_storename_newest_data(cls, db: Session, filter: dict):
        unionprice = cls.get_unionprice_for_storename_newest_data(filter=filter)
        stmt = cls.get_storename_newest_data_base(unionprice=unionprice)
        stmt = cls.__set_group_filter(filter, stmt)
        stmt = cls.__set_act_filter(filter, stmt)
        stmt = cls.__set_in_stock_filter_for_storename_newest(
            filter=filter, stmt=stmt, unionprice=unionprice
        )
        stmt = cls.__set_price_range_filter_for_storename_newest(
            filter=filter, stmt=stmt, unionprice=unionprice
        )
        stmt = cls.__set_extract_sort_filter(
            filter=filter, stmt=stmt, unionprice=unionprice
        )
        return db.execute(stmt).all()

    @classmethod
    def get_storename_newest_data_base(cls, unionprice):
        base = (
            select(
                Item.item_id,
                Item.name,
                unionprice.c.url_id,
                Url.urlpath,
                utc_to_jst_datetime_for_query(unionprice.c.created_at).label(
                    "created_at"
                ),
                unionprice.c.price.label("price"),
                unionprice.c.salename,
                unionprice.c.trendrate,
                unionprice.c.storename,
                NewestItem.lowestprice,
                cls.actcheck.c.act,
            )
            .select_from(unionprice)
            .join(
                UrlInItem,
                unionprice.c.url_id == UrlInItem.url_id,
            )
            .join(Item, Item.item_id == UrlInItem.item_id)
            .join(
                Url,
                unionprice.c.url_id == Url.url_id,
            )
            .join(NewestItem, NewestItem.item_id == Item.item_id)
            .join(
                cls.actcheck,
                cls.actcheck.c.item_id == Item.item_id,
            )
        )
        return base

    @classmethod
    def get_unionprice_for_storename_newest_data(cls, filter: dict):
        storename = cls.get_extract_storename_in_filter(filter)

        newest = (
            select(func.max(utc_to_jst_date_for_query(PriceLog_2days.created_at)))
            .where(PriceLog_2days.storename == storename)
            .scalar_subquery()
        )
        newest_data = (
            select(PriceLog_2days)
            .where(utc_to_jst_date_for_query(PriceLog_2days.created_at) == newest)
            .where(PriceLog_2days.storename == storename)
            .cte("newest_data")
        )
        used = (
            select(
                newest_data.c.log_id,
                newest_data.c.url_id,
                newest_data.c.usedprice.label("price"),
                newest_data.c.storename,
                newest_data.c.salename,
                newest_data.c.trendrate,
                newest_data.c.created_at,
            )
            .order_by(newest_data.c.usedprice.asc())
            .cte("used")
        )
        new = (
            select(
                newest_data.c.log_id,
                newest_data.c.url_id,
                newest_data.c.newprice.label("price"),
                newest_data.c.storename,
                newest_data.c.salename,
                newest_data.c.trendrate,
                newest_data.c.created_at,
            )
            .where(newest_data.c.log_id.notin_(select(used.c.log_id)))
            .order_by(newest_data.c.newprice.asc())
            .cte("new")
        )
        unionprice = select(used).union(new.select()).cte("unionprice")

        return unionprice

    @classmethod
    def get_extract_storename_in_filter(cls, filter: dict):
        if (
            fqn.EX_STORE.value not in filter.keys()
            or int(filter[fqn.EX_STORE.value]) < 0
        ):
            return ""

        stmt = (
            select(Store.storename)
            .where(Store.store_id == int(filter[fqn.EX_STORE.value]))
            .scalar_subquery()
        )
        return stmt

    @classmethod
    def __set_extract_sort_filter(cls, filter: dict, stmt, unionprice):
        if fqn.ESSORT.value not in filter.keys() or int(filter[fqn.ESSORT.value]) < 0:
            return stmt
        fnum = int(filter[fqn.ESSORT.value])
        if fnum == ExtractStoreSortName.OLD_ITEM.id:
            stmt = stmt.order_by(Item.item_id.asc())
            return stmt
        if fnum == ExtractStoreSortName.NEW_ITEM.id:
            stmt = stmt.order_by(Item.item_id.desc())
            return stmt
        if fnum == ExtractStoreSortName.LOW_PRICE.id:
            stmt = stmt.order_by(unionprice.c.price.label("price").asc())
            return stmt
        if fnum == ExtractStoreSortName.HIGH_PRICE.id:
            stmt = stmt.order_by(unionprice.c.price.label("price").desc())
            return stmt
        if fnum == ExtractStoreSortName.ITEM_NAME.id:
            stmt = stmt.order_by(Item.name.asc())
            return stmt
        if fnum == ExtractStoreSortName.LOW_TRENDRATE.id:
            stmt = stmt.order_by(text_to_decimal(unionprice.c.trendrate).asc())
            return stmt
        if fnum == ExtractStoreSortName.HIGH_TRENDRATE.id:
            stmt = stmt.order_by(text_to_decimal(unionprice.c.trendrate).desc())
            return stmt
        if fnum == ExtractStoreSortName.OLD_UPDATE_TIME.id:
            stmt = stmt.order_by(unionprice.c.created_at.asc())
            return stmt
        if fnum == ExtractStoreSortName.NEW_UPDATE_TIME.id:
            stmt = stmt.order_by(unionprice.c.created_at.desc())
            return stmt
        if fnum == ExtractStoreSortName.LOW_LOWESTPRICE.id:
            stmt = stmt.order_by(NewestItem.lowestprice.asc())
            return stmt
        if fnum == ExtractStoreSortName.HIGH_LOWESTPRICE.id:
            stmt = stmt.order_by(NewestItem.lowestprice.desc())
            return stmt
        if (
            fnum == ExtractStoreSortName.CLOSEST_LOWESTPRICE.id
            or fnum == ExtractStoreSortName.FURTHEST_LOWESTPRICE.id
        ):
            diff_t = cls.get_diff_extract_query_between_newestprice_and_lowestprice(
                stmt
            ).cte("diff_t")
            if fnum == ExtractStoreSortName.CLOSEST_LOWESTPRICE.id:
                stmt = stmt.join(
                    diff_t,
                    and_(
                        diff_t.c.item_id == Item.item_id,
                        diff_t.c.price == unionprice.c.price,
                    ),
                ).order_by(diff_t.c.diff.asc(), Item.item_id.asc())
            else:
                stmt = stmt.join(
                    diff_t,
                    and_(
                        diff_t.c.item_id == Item.item_id,
                        diff_t.c.price == unionprice.c.price,
                    ),
                ).order_by(diff_t.c.diff.desc(), Item.item_id.asc())
            return stmt
        return stmt

    @classmethod
    def get_diff_extract_query_between_newestprice_and_lowestprice(cls, base):
        diffb = base.cte("diffb")
        stmt = select(
            diffb.c.item_id,
            diffb.c.price,
            (diffb.c.price - diffb.c.lowestprice).label("diff"),
        ).where(diffb.c.price > const_value.INIT_PRICE)
        return stmt

    @classmethod
    def __set_in_stock_filter_for_storename_newest(cls, filter: dict, stmt, unionprice):
        if (
            fqn.ZAIKO.value not in filter.keys()
            or int(filter[fqn.ZAIKO.value]) != FilterOnOff.ON
        ):
            return stmt
        return stmt.where(unionprice.c.price > const_value.INIT_PRICE)

    @classmethod
    def __set_price_range_filter_for_storename_newest(
        cls, filter: dict, stmt, unionprice
    ):
        if fqn.PRMIN.value in filter.keys() and fqn.PRMAX.value in filter.keys():
            min = int(filter[fqn.PRMIN.value])
            max = int(filter[fqn.PRMAX.value])
            if min == max:
                stmt = stmt.where(unionprice.c.price == min)
                return stmt
            if min > max:
                return stmt
            stmt = stmt.where(unionprice.c.price >= min).where(
                unionprice.c.price <= max
            )
            return stmt
        if fqn.PRMIN.value in filter.keys():
            stmt = stmt.where(unionprice.c.price >= int(filter[fqn.PRMIN.value]))
            return stmt
        if fqn.PRMAX.value in filter.keys():
            stmt = stmt.where(unionprice.c.price <= int(filter[fqn.PRMAX.value]))
            return stmt
        return stmt

    @classmethod
    def update_by_deleting_url(cls, db: Session, url_id: int):
        stmt = (
            update(NewestItem)
            .where(NewestItem.url_id == url_id)
            .values(
                url_id=None,
                newestprice=const_value.INIT_PRICE,
                storename="",
                taxin="0",
                onsale="0",
                salename=None,
                trendrate=0,
            )
        )
        db.execute(stmt)
        db.commit()

    @classmethod
    def get_raw_newest_data_all(cls, db: Session):
        return db.scalars(select(NewestItem)).all()


class GroupQuery:
    @classmethod
    def add_group(cls, db: Session, name: str) -> int:
        g = Group(groupname=name)
        db.add(g)
        db.commit()
        db.refresh(g)
        return g.group_id

    @classmethod
    def get_all(cls, db: Session):
        return db.scalars(select(Group))

    @classmethod
    def get_group_by_name(cls, db: Session, name: str):
        stmt = select(Group).where(Group.groupname == name)
        return db.execute(stmt).one_or_none()

    @classmethod
    def get_group_by_group_id(cls, db: Session, gid: int):
        stmt = select(Group).where(Group.group_id == gid)
        return db.scalar(stmt)

    @classmethod
    def get_group_item_by_group_id(cls, db: Session, group_id: int):
        stmt = select(GroupItem).where(GroupItem.group_id == group_id)
        return db.scalars(stmt).all()

    @classmethod
    def update_group_name(cls, db: Session, group_id: int, name: str):
        stmt = update(Group).where(Group.group_id == group_id).values(groupname=name)
        db.execute(stmt)
        db.commit()

    @classmethod
    def update_group_item(cls, db: Session, group_id: int, item_list: list[int]):
        current_gilist = cls.get_group_item_by_group_id(db, group_id=group_id)
        current_item_id_list = [gi.item_id for gi in current_gilist]

        def __get_del_item_id_list():
            results: list[int] = []
            for item_id in current_item_id_list:
                if item_id not in item_list:
                    results.append(item_id)
            return results

        if len(current_item_id_list) != 0:
            del_item_id_list: list[int] = __get_del_item_id_list()
            cls.__del_group_items(db, group_id=group_id, item_id_list=del_item_id_list)

        def __get_add_item_id_list():
            results: list[int] = []
            for item_id in item_list:
                if item_id not in current_item_id_list:
                    results.append(item_id)
            return results

        add_item_id_list: list[int] = __get_add_item_id_list()
        if len(add_item_id_list) > 0:
            cls.__add_group_items(db, group_id=group_id, item_id_list=add_item_id_list)

    @classmethod
    def __del_group_items(cls, db: Session, group_id: int, item_id_list: list[int]):
        stmt = (
            delete(GroupItem)
            .where(GroupItem.group_id == group_id)
            .where(GroupItem.item_id.in_(item_id_list))
        )
        db.execute(stmt)
        db.commit()

    @classmethod
    def __add_group_items(cls, db: Session, group_id: int, item_id_list: list[int]):
        gi_list = [
            GroupItem(group_id=group_id, item_id=item_id) for item_id in item_id_list
        ]
        db.add_all(gi_list)
        db.commit()
        for gi in gi_list:
            db.refresh(gi)

    @classmethod
    def del_group(cls, db: Session, group_id: int):
        cls.__del_group_items_by_group_id(db, group_id)
        stmt = delete(Group).where(Group.group_id == group_id)
        db.execute(stmt)
        db.commit()

    @classmethod
    def __del_group_items_by_group_id(cls, db: Session, group_id: int):
        stmt = delete(GroupItem).where(GroupItem.group_id == group_id)
        db.execute(stmt)
        db.commit()


class ItemQuery:
    @classmethod
    def add(cls, db: Session, name: str = "", item_id: int | None = None) -> int:
        if item_id:
            if cls.get_item(db, item_id=item_id):
                return item_id
            i = Item(item_id=item_id, name=name)
        else:
            i = Item(name=name)
        db.add(i)
        db.commit()
        db.refresh(i)
        return i.item_id

    @classmethod
    def get_item(cls, db: Session, item_id: int) -> Item:
        stmt = select(Item).where(Item.item_id == item_id)
        return db.scalar(stmt)

    @classmethod
    def get_most_recent_old_price_of_2days_by_item_id(cls, db: Session, item_id: int):
        target_url = select(UrlInItem.url_id).where(UrlInItem.item_id == item_id)
        return cls.__get_most_recent_old_price_of_2days(db, target_url=target_url)

    @classmethod
    def get_most_recent_old_price_of_2days_by_url_id(cls, db: Session, url_id: int):
        return cls.__get_most_recent_old_price_of_2days(db, target_url=[url_id])

    @classmethod
    def __get_most_recent_old_price_of_2days(cls, db: Session, target_url):
        pricelist = (
            select(
                PriceLog_2days.created_at,
                PriceLog_2days.newprice,
                PriceLog_2days.usedprice,
            )
            .where(PriceLog_2days.url_id.in_(target_url))
            .where(text_to_boolean(PriceLog_2days.issuccess) == "1")
            .where(
                utc_to_jst_date_for_query(PriceLog_2days.created_at)
                <= get_jst_date_for_query(interval_days=INTERVAL_YESTERDAY)
            )
            .subquery("pricelist")
        )

        return cls.__get_old_min_pricelog(db, price_list_query=pricelist)

    @classmethod
    def __get_old_min_pricelog(cls, db: Session, price_list_query):
        pricelist = price_list_query
        max_date = select(
            func.max(utc_to_jst_date_for_query(pricelist.c.created_at))
        ).scalar_subquery()
        lasttime = (
            select(pricelist.c.newprice, pricelist.c.usedprice)
            .where(utc_to_jst_date_for_query(pricelist.c.created_at) == max_date)
            .subquery("lasttime")
        )
        newlowest = select(func.min(lasttime.c.newprice).label("price")).where(
            lasttime.c.newprice != const_value.INIT_PRICE
        )
        usedlowest = select(func.min(lasttime.c.usedprice).label("price")).where(
            lasttime.c.usedprice != const_value.INIT_PRICE
        )
        lowest = union(newlowest, usedlowest).subquery("lowest")
        stmt = select(func.min(lowest.c.price))
        return db.scalar(stmt)

    @classmethod
    def get_pricelog_2days_by_url_id(cls, db: Session, url_id: int):
        stmt = select(PriceLog_2days).where(PriceLog_2days.url_id == url_id)
        res = db.scalars(stmt).all()
        return res

    @classmethod
    def get_pricelog_by_url_id(cls, db: Session, url_id: int):
        stmt = select(PriceLog).where(PriceLog.url_id == url_id)
        res = db.scalars(stmt).all()
        return res

    @classmethod
    def upsert_pricelog(cls, db: Session, pldict: dict) -> bool:
        if "url_id" not in pldict:
            return False
        if cls.is_today_pricelog_2days_available(
            db,
            url_id=pldict["url_id"],
            storename=pldict["storename"],
            usedprice=pldict["usedprice"],
            newprice=pldict["newprice"],
        ):
            cls.__update_pricelog_2days_by_dict(db, pldict=pldict)
            return True
        cls.__add_pricelog_by_dict(db, pldict=pldict)
        return True

    @classmethod
    def is_today_pricelog_2days_available(
        cls,
        db: Session,
        url_id: int,
        storename: str = "",
        usedprice: int = -1,
        newprice: int = -1,
    ) -> bool:
        stmt = (
            select(PriceLog_2days)
            .where(PriceLog_2days.url_id == url_id)
            .where(PriceLog_2days.storename == storename)
            .order_by(PriceLog_2days.created_at.desc())
        )
        pl = db.scalar(stmt)
        if pl:
            if util.isLocalToday(
                util.utcTolocaltime(pl.created_at)
            ) and cls.__is_update_price(
                insert_used=usedprice,
                insert_new=newprice,
                db_new=pl.newprice,
                db_used=pl.usedprice,
            ):
                return True
        return False

    @classmethod
    def __is_update_price(
        cls, insert_new: int, insert_used: int, db_new: int, db_used: int
    ):
        if (insert_new != db_new and insert_new != const_value.INIT_PRICE) or (
            insert_used != db_used and insert_used != const_value.INIT_PRICE
        ):
            return True
        return False

    @classmethod
    def update_pricelog_2days_by_dict_and_log_id(
        cls, db: Session, pldict: dict, log_id: int
    ):
        stmt = (
            update(PriceLog_2days).where(PriceLog_2days.log_id == log_id).values(pldict)
        )
        db.execute(stmt)
        db.commit()

    @classmethod
    def __update_pricelog_2days_by_dict(cls, db: Session, pldict: dict) -> None:
        url_id = pldict["url_id"]
        storename = pldict["storename"]
        target = (
            select(PriceLog_2days)
            .where(PriceLog_2days.url_id == url_id)
            .where(PriceLog_2days.storename == storename)
            .order_by(PriceLog_2days.created_at.desc())
            .limit(1)
        )
        """
        update_pricelog = (
            update(PriceLog)
            .where(PriceLog.url_id == url_id)
            .where(PriceLog.storename == storename)
            .where(PriceLog.created_at == target.c.created_at)
            .values(pldict)
        )
        """
        update_pricelog_2dasy = (
            update(PriceLog_2days)
            .where(PriceLog_2days.url_id == url_id)
            .where(PriceLog_2days.storename == storename)
            .where(PriceLog_2days.created_at == target.c.created_at)
            .values(pldict)
        )
        # ses.execute(update_pricelog)
        db.execute(update_pricelog_2dasy)
        db.commit()

    @classmethod
    def add_pricelog_2days_by_dict(cls, db: Session, pldict: dict):
        insert_pricelog_2days = insert(PriceLog_2days).values(pldict)
        db.execute(insert_pricelog_2days)
        db.commit()

    @classmethod
    def __add_pricelog_by_dict(cls, db: Session, pldict: dict) -> None:
        insert_pricelog = insert(PriceLog).values(pldict)
        insert_pricelog_2days = insert(PriceLog_2days).values(pldict)
        db.execute(insert_pricelog)
        db.execute(insert_pricelog_2days)
        db.commit()

    @classmethod
    def update_items_name_by_item_id(cls, db: Session, item_id: int, name: str) -> None:
        if item_id == const_value.NONE_ID:
            return
        stmt = update(Item).where(Item.item_id == item_id).values(name=name)
        db.execute(stmt)
        db.commit()

    @classmethod
    def update_items_name_by_url_id(
        cls, db: Session, url_id: int, uniqname: str
    ) -> None:
        if url_id == const_value.NONE_ID or len(uniqname) == 0:
            return
        itemids = NewestQuery.get_item_id_from_urlinitem_by_url_id(db, url_id=url_id)
        if not itemids or len(itemids) == 0:
            return
        for itemid in itemids:
            iobj = db.get(Item, itemid)
            if iobj and cls.__is_update_items_name(iobj):
                stmt = update(Item).where(Item.item_id == itemid).values(name=uniqname)
                db.execute(stmt)
            db.refresh(iobj)
        db.commit()

    @classmethod
    def __is_update_items_name(cls, iobj: Item):
        if iobj.name == "":
            return True
        return False

    @classmethod
    def get_item_pricelog_by_item_id_1year(
        cls,
        db: Session,
        item_id: int,
        result_limit: int | None = None,
        days: int | None = None,
        storename: str = "",
    ):
        stmt = (
            select(
                Item.item_id,
                PriceLog.uniqname,
                Url.url_id,
                Url.urlpath,
                utc_to_jst_datetime_for_query(PriceLog.created_at).label("created_at"),
                PriceLog.usedprice,
                PriceLog.newprice,
                PriceLog.salename,
                PriceLog.storename,
                PriceLog.issuccess,
                PriceLog.trendrate,
                UrlInItem.active,
            )
            .select_from(Item)
            .join(UrlInItem, UrlInItem.item_id == item_id)
            .join(Url, UrlInItem.url_id == Url.url_id)
            .join(PriceLog, PriceLog.url_id == Url.url_id)
            .where(Item.item_id == item_id)
            .order_by(PriceLog.created_at.desc())
        )
        if days and days <= 0:
            stmt = stmt.where(
                utc_to_jst_datetime_for_query(PriceLog.created_at)
                >= get_jst_datetime_for_query(interval_days=days)
            )
        if storename:
            stmt = stmt.where(PriceLog.storename == storename)
        if result_limit and result_limit > 0:
            stmt = stmt.limit(result_limit)
        return db.execute(stmt).all()

    @classmethod
    def get_storename_by_item_id_1year(
        cls,
        db: Session,
        item_id: int,
        days: int | None = None,
    ):
        stmt = (
            select(
                PriceLog.storename,
            )
            .select_from(Item)
            .join(UrlInItem, UrlInItem.item_id == item_id)
            .join(Url, UrlInItem.url_id == Url.url_id)
            .join(PriceLog, PriceLog.url_id == Url.url_id)
            .where(Item.item_id == item_id)
            .group_by(PriceLog.storename)
        )
        if days and days <= 0:
            stmt = stmt.where(
                utc_to_jst_datetime_for_query(PriceLog.created_at)
                >= get_jst_datetime_for_query(interval_days=days)
            )
        return db.scalars(stmt).all()

    @classmethod
    def get_daily_min_used_pricelog_by_item_id_and_since_year_ago(
        cls, db: Session, item_id: int, year: int
    ):
        subq = (
            select(
                utc_to_jst_date_for_query(PriceLog.created_at).label("created_at"),
                PriceLog.usedprice,
            )
            .select_from(PriceLog)
            .join(UrlInItem, UrlInItem.url_id == PriceLog.url_id)
            .where(UrlInItem.item_id == item_id)
            .where(
                utc_to_jst_datetime_for_query(PriceLog.created_at)
                >= get_jst_datetime_for_query(
                    interval_years=year * INTERVAL_ONE_YEARS_AGO
                )
            )
            .where(PriceLog.usedprice > 0)
        ).subquery("subq")
        stmt = select(
            subq.c.created_at, func.min(subq.c.usedprice).label("price")
        ).group_by(subq.c.created_at)
        return db.execute(stmt).all()

    @classmethod
    def get_daily_min_new_pricelog_by_item_id_and_since_year_ago(
        cls, db: Session, item_id: int, year: int
    ):
        subq = (
            select(
                utc_to_jst_date_for_query(PriceLog.created_at).label("created_at"),
                PriceLog.newprice,
            )
            .select_from(PriceLog)
            .join(UrlInItem, UrlInItem.url_id == PriceLog.url_id)
            .where(UrlInItem.item_id == item_id)
            .where(
                utc_to_jst_datetime_for_query(PriceLog.created_at)
                >= get_jst_datetime_for_query(
                    interval_years=year * INTERVAL_ONE_YEARS_AGO
                )
            )
            .where(PriceLog.newprice > 0)
        ).subquery("subq")
        stmt = select(
            subq.c.created_at, func.min(subq.c.newprice).label("price")
        ).group_by(subq.c.created_at)
        return db.execute(stmt).all()

    @classmethod
    def get_latest_price_by_item_id_list(cls, db: Session, item_id_list: list[int]):
        new_price = (
            select(
                Item.name.label("itemname"),
                PriceLog_2days.storename,
                PriceLog_2days.newprice.label("price"),
            )
            .join(UrlInItem, UrlInItem.url_id == PriceLog_2days.url_id)
            .where(UrlInItem.active == "True")
            .where(UrlInItem.item_id.in_(item_id_list))
            .where(
                utc_to_jst_date_for_query(PriceLog_2days.created_at)
                >= get_jst_date_for_query()
            )
            .where(text_to_boolean(PriceLog_2days.issuccess) == "1")
            .where(PriceLog_2days.storename != "")
            .where(PriceLog_2days.newprice > 0)
            .join(Item, Item.item_id == UrlInItem.item_id)
        )
        used_price = (
            select(
                Item.name.label("itemname"),
                PriceLog_2days.storename,
                PriceLog_2days.usedprice.label("price"),
            )
            .join(UrlInItem, UrlInItem.url_id == PriceLog_2days.url_id)
            .where(UrlInItem.active == "True")
            .where(UrlInItem.item_id.in_(item_id_list))
            .where(
                utc_to_jst_date_for_query(PriceLog_2days.created_at)
                >= get_jst_date_for_query()
            )
            .where(text_to_boolean(PriceLog_2days.issuccess) == "1")
            .where(PriceLog_2days.storename != "")
            .where(PriceLog_2days.usedprice > 0)
            .join(Item, Item.item_id == UrlInItem.item_id)
        )
        stmt = union(new_price, used_price)
        return db.execute(stmt).all()

    @classmethod
    def get_count_of_pricelog_2days_for_today_by_item_id(
        cls, db: Session, item_id_list: list[int]
    ) -> int:
        stmt = (
            select(func.count(PriceLog_2days.log_id))
            .join(UrlInItem, UrlInItem.url_id == PriceLog_2days.url_id)
            .where(UrlInItem.item_id.in_(item_id_list))
            .where(
                utc_to_jst_date_for_query(PriceLog_2days.created_at)
                >= get_jst_date_for_query()
            )
        )
        return db.scalar(stmt)

    @classmethod
    def get_current_storename_list_by_item_id(
        cls, db: Session, item_id_list: list[int]
    ):
        stmt = (
            select(PriceLog_2days.storename)
            .join(UrlInItem, UrlInItem.url_id == PriceLog_2days.url_id)
            .where(UrlInItem.active == "True")
            .where(UrlInItem.item_id.in_(item_id_list))
            .where(
                utc_to_jst_date_for_query(PriceLog_2days.created_at)
                >= get_jst_date_for_query()
            )
            .where(text_to_boolean(PriceLog_2days.issuccess) == "1")
            .where(PriceLog_2days.storename != "")
            .group_by(PriceLog_2days.storename)
        )
        return db.execute(stmt).all()

    @classmethod
    def delete_item_relation_by_item_id(cls, db: Session, item_id: int):
        groupitem_del = delete(GroupItem).where(GroupItem.item_id == item_id)
        urlinitem_del = delete(UrlInItem).where(UrlInItem.item_id == item_id)
        newest_del = delete(NewestItem).where(NewestItem.item_id == item_id)
        item_del = delete(Item).where(Item.item_id == item_id)
        db.execute(groupitem_del)
        db.execute(urlinitem_del)
        db.execute(newest_del)
        db.execute(item_del)
        db.commit()

    @classmethod
    def get_newest_storenames(cls, db: Session):
        max_date = select(
            func.max(utc_to_jst_date_for_query(PriceLog_2days.created_at))
        ).scalar_subquery()
        stmt = (
            select(PriceLog_2days.storename)
            .where(utc_to_jst_date_for_query(PriceLog_2days.created_at) == max_date)
            .group_by(PriceLog_2days.storename)
        )
        return db.execute(stmt).all()

    @classmethod
    def get_item_and_url_localtime(cls, db: Session, filter: dict):
        isactive = get_act_filter(filter)
        stmt = (
            select(
                Item.item_id,
                Item.name,
                Url.url_id,
                Url.urlpath,
                UrlInItem.active,
                utc_to_jst_datetime_for_query(Item.created_at).label("created_at"),
            )
            .select_from(Item)
            .join(UrlInItem, UrlInItem.item_id == Item.item_id, isouter=True)
            .join(Url, UrlInItem.url_id == Url.url_id, isouter=True)
        )
        if isactive:
            stmt = stmt.where(UrlInItem.active == isactive.value)
        stmt = cls.__set_group_filter(filter=filter, stmt=stmt)
        stmt = cls.__set_purchasesort_filter(filter=filter, stmt=stmt)
        return db.execute(stmt).all()

    @classmethod
    def __set_group_filter(cls, filter: dict, stmt):
        if fqn.GID.value not in filter.keys() or int(filter[fqn.GID.value]) < 0:
            return stmt
        stmt = stmt.join(GroupItem, GroupItem.item_id == Item.item_id).where(
            GroupItem.group_id == int(filter[fqn.GID.value])
        )
        return stmt

    @classmethod
    def __set_purchasesort_filter(cls, filter: dict, stmt):
        if fqn.PSORT.value not in filter.keys() or int(filter[fqn.PSORT.value]) < 0:
            stmt = stmt.order_by(Item.item_id.asc())
            return stmt
        fnum = int(filter[fqn.PSORT.value])
        if fnum == ItemPurchaseSortName.OLD_ITEM.id:
            stmt = stmt.order_by(Item.item_id.asc())
            return stmt
        if fnum == ItemPurchaseSortName.NEW_ITEM.id:
            stmt = stmt.order_by(Item.item_id.desc())
            return stmt
        if fnum == ItemPurchaseSortName.ITEM_NAME.id:
            stmt = stmt.order_by(Item.name.asc())
            return stmt

        return stmt


class OrganizerQuery:
    @classmethod
    def get_recent_pricelog_by_url_id(cls, db: Session, url_id: int):
        sub = (
            select(PriceLog)
            .where(PriceLog.url_id == url_id)
            .order_by(PriceLog.created_at.desc())
            .subquery()
        )
        stmt = select(sub).group_by(sub.c.storename)
        return db.execute(stmt).all()

    @classmethod
    def get_old_pricelog_before_days(cls, db: Session, days: int):
        get_old = select(PriceLog).where(
            utc_to_jst_datetime_for_query(PriceLog.created_at)
            <= get_jst_datetime_for_query(interval_days=days * INTERVAL_YESTERDAY)
        )
        return db.scalars(get_old).all()

    @classmethod
    def get_old_pricelog_by_days(cls, db: Session, days: int):
        get_old = select(PriceLog).where(
            utc_to_jst_date_for_query(PriceLog.created_at)
            == get_jst_date_for_query(interval_days=days * INTERVAL_YESTERDAY)
        )
        return db.scalars(get_old).all()

    @classmethod
    def get_old_pricelog_2days_by_days(cls, db: Session, days: int):
        get_old = select(PriceLog_2days).where(
            utc_to_jst_date_for_query(PriceLog_2days.created_at)
            == get_jst_date_for_query(interval_days=days * INTERVAL_YESTERDAY)
        )
        return db.scalars(get_old).all()

    @classmethod
    def get_pricelog_2days_all(cls, db: Session):
        stmt = select(PriceLog_2days)
        return db.scalars(stmt).all()

    @classmethod
    def get_pricelog_2days_today(cls, db: Session):
        stmt = select(PriceLog_2days).where(
            utc_to_jst_date_for_query(PriceLog_2days.created_at)
            == get_jst_date_for_query()
        )
        return db.scalars(stmt).all()

    @classmethod
    def get_pricelog_today(cls, db: Session):
        stmt = select(PriceLog).where(
            utc_to_jst_date_for_query(PriceLog.created_at) == get_jst_date_for_query()
        )
        return db.scalars(stmt).all()

    @classmethod
    def delete_old_pricelog_before_days(cls, db: Session, days: int):
        delete_old = delete(PriceLog).where(
            utc_to_jst_datetime_for_query(PriceLog.created_at)
            <= get_jst_datetime_for_query(interval_days=days * INTERVAL_YESTERDAY)
        )
        db.execute(delete_old)
        db.commit()

    @classmethod
    def delete_old_pricelog_2days_before_days(cls, db: Session, days: int):
        delete_old = delete(PriceLog_2days).where(
            utc_to_jst_datetime_for_query(PriceLog_2days.created_at)
            <= get_jst_datetime_for_query(interval_days=days * INTERVAL_YESTERDAY)
        )
        db.execute(delete_old)
        db.commit()

    @classmethod
    def delete_pricelog_2days_by_log_id_list(cls, db: Session, log_id_list: list[int]):
        stmt = delete(PriceLog_2days).where(PriceLog_2days.log_id.in_(log_id_list))
        db.execute(stmt)
        db.commit()

    @classmethod
    def delete_pricelog_by_log_id_list(cls, db: Session, log_id_list: list[int]):
        stmt = delete(PriceLog).where(PriceLog.log_id.in_(log_id_list))
        db.execute(stmt)
        db.commit()

    @classmethod
    def add_price_log_by_dict_list(cls, db: Session, pricelog_dict_list: list[dict]):
        stmt = insert(PriceLog).values(pricelog_dict_list)
        db.execute(stmt)
        db.commit()

    @classmethod
    def add_price_log_2days_by_dict_list(
        cls, db: Session, pricelog_dict_list: list[dict]
    ):
        stmt = insert(PriceLog_2days).values(pricelog_dict_list)
        db.execute(stmt)
        db.commit()

    @classmethod
    def update_pricelog_by_dict_list(cls, db: Session, pricelog_dict_list: list[dict]):
        for pricelog_dict in pricelog_dict_list:
            log_id = pricelog_dict.pop("log_id", None)
            if log_id is None:
                continue
            stmt = (
                update(PriceLog).where(PriceLog.log_id == log_id).values(pricelog_dict)
            )
            db.execute(stmt)
        db.commit()


class OldItemQuery:
    @classmethod
    def add_pricelog_of_old_by_dict_list(
        cls, db: Session, pricelog_dict_list: list[dict]
    ):
        stmt = insert(PriceLog).values(pricelog_dict_list)
        db.execute(stmt)
        db.commit()

    @classmethod
    def delete_pricelog_by_url(cls, db: Session, url_id: int):
        stmt = delete(PriceLog).where(PriceLog.url_id == url_id)
        db.execute(stmt)
        db.commit()


class UrlQuery:
    @classmethod
    def add_url(cls, db: Session, urlpath: str) -> int:
        if not urlpath:
            raise RuntimeError
        return cls.__add_url(db, urlpath=urlpath)

    @classmethod
    def add_url_and_urlinitem(
        cls, db: Session, urlpath: str, item_id: int | None = None
    ) -> int:
        if not urlpath:
            raise RuntimeError

        url_id = cls.__add_url(db, urlpath=urlpath)
        if not item_id:
            return url_id

        cls.__add_urlinitem(db, url_id=url_id, item_id=item_id)
        return url_id

    @classmethod
    def add_urlinitem(cls, db: Session, url_id: int, item_id: int) -> None:
        cls.__add_urlinitem(db, url_id=url_id, item_id=item_id)

    @classmethod
    def __add_url(cls, db: Session, urlpath: str) -> int:
        u_obj = cls.get_url(db, urlpath=urlpath)
        if u_obj:
            return u_obj.url_id
        u = Url(urlpath=urlpath)
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.url_id

    @classmethod
    def __add_urlinitem(cls, db: Session, url_id: int, item_id: int) -> None:
        uii_obj = cls.__get_urlinitem(db, url_id=url_id, item_id=item_id)
        if uii_obj:
            return
        uii = UrlInItem(item_id=item_id, url_id=url_id, active=UrlActive.ACTIVE.value)
        db.add(uii)
        db.commit()
        db.refresh(uii)

    @classmethod
    def update_url_active(
        cls, db: Session, item_id: int, url_id: int, isactive: UrlActive
    ) -> None:
        stmt = (
            update(UrlInItem)
            .where(UrlInItem.url_id == url_id)
            .where(UrlInItem.item_id == item_id)
            .values(active=isactive.value)
        )
        db.execute(stmt)
        db.commit()

    @classmethod
    def update_url_active_by_url_id(cls, db: Session, url_id: int, isactive: UrlActive):
        stmt = (
            update(UrlInItem)
            .where(UrlInItem.url_id == url_id)
            .values(active=isactive.value)
        )
        db.execute(stmt)
        db.commit()

    @classmethod
    def update_url_active_all_by_item_id(
        cls, db: Session, item_id: int, isactive: UrlActive
    ) -> None:
        stmt = (
            update(UrlInItem)
            .where(UrlInItem.item_id == item_id)
            .values(active=isactive.value)
        )
        db.execute(stmt)
        db.commit()

    @classmethod
    def get_url(cls, db: Session, urlpath: str) -> Url:
        stmt = select(Url).where(Url.urlpath == urlpath)
        return db.scalar(stmt)

    @classmethod
    def get_url_all(cls, db: Session):
        stmt = select(Url)
        return db.scalars(stmt)

    @classmethod
    def get_urlinitem(cls, db: Session, url_id: int, item_id: int) -> UrlInItem:
        return cls.__get_urlinitem(db, url_id=url_id, item_id=item_id)

    @classmethod
    def __get_urlinitem(cls, db: Session, url_id, item_id) -> UrlInItem:
        stmt = (
            select(UrlInItem)
            .where(UrlInItem.url_id == url_id)
            .where(UrlInItem.item_id == item_id)
        )
        return db.scalar(stmt)

    @classmethod
    def get_act_items_url(cls, db: Session):
        stmt = (
            select(UrlInItem.item_id, Url.urlpath)
            .join(Url, Url.url_id == UrlInItem.url_id, isouter=True)
            .where(UrlInItem.active == UrlActive.ACTIVE.value)
        )
        return db.execute(stmt).all()

    @classmethod
    def get_act_urlinfo_by_item_id(cls, db: Session, item_id: int):
        stmt = (
            select(UrlInItem.url_id, Url.urlpath, UrlInItem.active)
            .join(Url, UrlInItem.url_id == Url.url_id)
            .where(UrlInItem.item_id == item_id)
            .where(UrlInItem.active == UrlActive.ACTIVE.value)
        )
        return db.execute(stmt).all()

    @classmethod
    def get_urlinfo_by_item_id(cls, db: Session, item_id: int):
        stmt = (
            select(UrlInItem.url_id, Url.urlpath, UrlInItem.active)
            .join(Url, UrlInItem.url_id == Url.url_id)
            .where(UrlInItem.item_id == item_id)
        )
        return db.execute(stmt).all()

    @classmethod
    def delete_urlinitem(cls, db: Session, item_id: int, url_id: int):
        stmt = (
            delete(UrlInItem)
            .where(UrlInItem.item_id == item_id)
            .where(UrlInItem.url_id == url_id)
        )
        db.execute(stmt)
        db.commit()

    @classmethod
    def get_url_and_item_comb_list_in_local_time(cls, db: Session, filter: dict):
        stmt = (
            select(
                Url.url_id,
                Url.urlpath,
                PriceLog_2days.uniqname,
                utc_to_jst_datetime_for_query(Url.created_at).label(
                    "registration_date"
                ),
                utc_to_jst_datetime_for_query(PriceLog_2days.created_at).label(
                    "created_at"
                ),
                UrlInItem.item_id,
                Item.name.label("itemname"),
                UrlInItem.active,
            )
            .select_from(Url)
            .join(UrlInItem, Url.url_id == UrlInItem.url_id, isouter=True)
            .join(PriceLog_2days, Url.url_id == PriceLog_2days.url_id, isouter=True)
            .join(Item, UrlInItem.item_id == Item.item_id, isouter=True)
        )
        isactive = get_act_filter(filter)
        if isactive:
            stmt = stmt.where(UrlInItem.active == isactive.value)
        stmt = cls.__set_urlsort_filter(filter, stmt)

        return db.execute(stmt).all()

    @classmethod
    def __set_urlsort_filter(cls, filter: dict, stmt):
        if fqn.USORT.value not in filter.keys() or int(filter[fqn.USORT.value]) < 0:
            stmt = stmt.order_by(Url.url_id.asc())
            return stmt
        fnum = int(filter[fqn.USORT.value])
        match fnum:
            case UrlSortName.URLID_ASC.id:
                stmt = stmt.order_by(Url.url_id.asc())
                return stmt
            case UrlSortName.URLID_DESC.id:
                stmt = stmt.order_by(Url.url_id.desc())
                return stmt
            case UrlSortName.ITEMID_ASC.id:
                stmt = stmt.order_by(UrlInItem.item_id.asc())
                return stmt
            case UrlSortName.ITEMID_DESC.id:
                stmt = stmt.order_by(UrlInItem.item_id.desc())
                return stmt
            case UrlSortName.UPDATE_TIME_ASC.id:
                stmt = stmt.order_by(PriceLog_2days.created_at.asc())
                return stmt
            case UrlSortName.UPDATE_TIME_DESC.id:
                stmt = stmt.order_by(PriceLog_2days.created_at.desc())
                return stmt
        return stmt

    @classmethod
    def get_url_id_by_url(cls, db: Session, url: str):
        return db.scalar(select(Url.url_id).where(Url.urlpath == url))

    @classmethod
    def delete_all_related_by_url(cls, db: Session, url_id: int):
        delete_pricelog = delete(PriceLog).where(PriceLog.url_id == url_id)
        db.execute(delete_pricelog)
        delete_pricelog_2days = delete(PriceLog_2days).where(
            PriceLog_2days.url_id == url_id
        )
        db.execute(delete_pricelog_2days)
        delete_urlinitem = delete(UrlInItem).where(UrlInItem.url_id == url_id)
        db.execute(delete_urlinitem)
        delete_url = delete(Url).where(Url.url_id == url_id)
        db.execute(delete_url)
        db.commit()


class AnalysisQuery:
    @classmethod
    def get_itemlog_from_day(cls, db: Session, days: int):
        stmt = (
            select(
                UrlInItem.item_id,
                PriceLog.url_id,
                UrlInItem.active,
                PriceLog.newprice,
                PriceLog.usedprice,
                PriceLog.storename,
                PriceLog.created_at,
            )
            .select_from(PriceLog)
            .join(UrlInItem, UrlInItem.url_id == PriceLog.url_id)
            .where(
                utc_to_jst_date_for_query(PriceLog.created_at)
                >= get_jst_date_for_query(interval_days=days)
            )
        )
        return db.execute(stmt).all()

    @classmethod
    def get_itemlog_period_datetime_from_day(cls, db: Session, days: int):
        stmt = select(
            func.min(PriceLog.created_at).label("start"),
            func.max(PriceLog.created_at).label("end"),
        ).where(
            utc_to_jst_date_for_query(PriceLog.created_at)
            >= get_jst_date_for_query(interval_days=days)
        )
        return db.execute(stmt).all()

    @classmethod
    def get_itemlog_by_period_date(cls, db: Session, start_jst: date, end_jst: date):
        date_list = [start_jst, end_jst]
        stmt = (
            select(
                UrlInItem.item_id,
                PriceLog.url_id,
                UrlInItem.active,
                PriceLog.newprice,
                PriceLog.usedprice,
                PriceLog.storename,
                PriceLog.created_at,
            )
            .select_from(PriceLog)
            .join(UrlInItem, UrlInItem.url_id == PriceLog.url_id)
            .where(utc_to_jst_date_for_query(PriceLog.created_at).in_(date_list))
        )
        return db.execute(stmt).all()


class AutoUpdateItem:
    @classmethod
    def get_pricelog_2days_count_by_date_range(
        cls, db: Session, start: datetime, end: datetime
    ):
        start_n = start.replace(tzinfo=None)
        end_n = end.replace(tzinfo=None)
        stmt = select(func.count(PriceLog_2days.log_id)).where(
            between(
                utc_to_jst_datetime_for_query(PriceLog_2days.created_at), start_n, end_n
            )
        )
        return db.scalar(stmt)


class PredictionQuery:

    @classmethod
    def get_stmt_pricelog_by_url_id_and_datetime_range(
        cls,
        url_id: int,
        start: datetime,
        end: datetime | None = None,
        is_not_zero_price: bool = True,
    ):
        stmt = select(PriceLog).where(PriceLog.url_id == url_id)
        if is_not_zero_price:
            stmt = stmt.where(PriceLog.usedprice > 0)
        if start.tzinfo is not None:
            start_n = start.astimezone(timezone.utc)
        else:
            start_n = start
        if end:
            if end.tzinfo is not None:
                end_n = end.astimezone(timezone.utc)
            else:
                end_n = end
            stmt = stmt.where(between(PriceLog.created_at, start_n, end_n))
        else:
            stmt = stmt.where(PriceLog.created_at >= start_n)
        return stmt

    @classmethod
    def get_stmt_pricelog_by_url_id_and_date_range(
        cls,
        url_id: int,
        start: datetime,
        end: datetime | None = None,
        is_not_zero_price: bool = True,
    ):
        start_n = start.replace(hour=0, minute=0, second=0, microsecond=0)
        if end:
            end_n = end.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            end_n = end
        return cls.get_stmt_pricelog_by_url_id_and_datetime_range(
            url_id=url_id, start=start_n, end=end_n, is_not_zero_price=is_not_zero_price
        )

    @classmethod
    def get_stmt_pricelog_by_item_id_and_datetime_range(
        cls,
        item_id: int,
        start: datetime,
        end: datetime | None = None,
        is_active: bool = True,
        is_not_zero_price: bool = True,
    ):
        stmt = (
            select(PriceLog)
            .select_from(PriceLog)
            .join(UrlInItem, UrlInItem.url_id == PriceLog.url_id)
            .where(UrlInItem.item_id == item_id)
        )
        if is_active:
            stmt = stmt.where(UrlInItem.active == UrlActive.ACTIVE.value)
        if is_not_zero_price:
            stmt = stmt.where(or_(PriceLog.usedprice > 0, PriceLog.newprice > 0))
        if start.tzinfo is not None:
            start_n = start.astimezone(timezone.utc)
        else:
            start_n = start
        if end:
            if end.tzinfo is not None:
                end_n = end.astimezone(timezone.utc)
            else:
                end_n = end
            stmt = stmt.where(between(PriceLog.created_at, start_n, end_n))
        else:
            stmt = stmt.where(PriceLog.created_at >= start_n)
        return stmt

    @classmethod
    def get_stmt_pricelog_by_item_id_and_date_range(
        cls,
        item_id: int,
        start: datetime,
        end: datetime | None = None,
        is_active: bool = True,
        is_not_zero_price: bool = True,
    ):
        start_n = start.replace(hour=0, minute=0, second=0, microsecond=0)
        if end:
            end_n = end.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            end_n = end
        return cls.get_stmt_pricelog_by_item_id_and_datetime_range(
            item_id=item_id,
            start=start_n,
            end=end_n,
            is_active=is_active,
            is_not_zero_price=is_not_zero_price,
        )

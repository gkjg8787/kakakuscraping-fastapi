from typing import List, Dict, Optional
from enum import Enum

from sqlalchemy import (
    select,
    insert,
    delete,
    update,
    union,
    func,
)
#from sqlalchemy.dialects.sqlite import insert as lite_insert

from sqlalchemy.sql import expression as exp
from sqlalchemy.orm import Session

from common import const_value, util
from common.filter_name import (
    FilterQueryName as fqn,
    ActFilterName,
    ItemSortName,
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
)

from html_parser.htmlparse import ParseItemInfo

#from common.stop_watch import stop_watch


class UrlActive(Enum):
    ACTIVE = 'True'
    INACTIVE = 'False' 

class NewestQuery:
    act_t = (
        select(
            UrlInItem.item_id,
            func.count(UrlInItem.url_id).label("act")
        )
        .where(UrlInItem.active==UrlActive.ACTIVE.value)
        .group_by(UrlInItem.item_id)
        .cte('act_t')
    )
    inact_t = (
        select(
            Item.item_id,
            exp.literal(0).label("act")
        )
        .where(Item.item_id.notin_(
                select(act_t.c.item_id)
        ))
        .group_by(Item.item_id)
        .cte('inact_t')
    )
    actcheck = (
        #union(act_t, inact_t).subquery("actcheck")
        select(act_t).union(inact_t.select()).cte('actcheck')
    )
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
        .join(NewestItem,
            Item.item_id == NewestItem.item_id,
            isouter=True)
        .join(Url,
            NewestItem.url_id == Url.url_id,
            isouter=True)
        .join(actcheck,
            actcheck.c.item_id == Item.item_id,
            isouter=True)
    )
    @classmethod
    def get_base_select(cls):
        return cls.base_select
    
    @classmethod
    def get_newest_data(cls, db :Session, filter:Dict):
        stmt = cls.get_newest_filter_statement(filter)
        return db.execute(stmt).all()
    
    @classmethod
    def get_newest_data_for_edit_group(cls, db :Session, filter:Dict):
        stmt = cls.get_base_select()
        stmt = cls.__set_act_filter(filter, stmt)
        stmt = cls.__set_eq_storename(filter, stmt)
        stmt = cls.__set_itemsort_filter(filter, stmt)
        return db.execute(stmt).all()
    
    @classmethod
    def get_newest_data_by_item_id(cls, db :Session, item_id:int):
        stmt = cls.get_base_select().where(Item.item_id == item_id)
        return db.execute(stmt).one_or_none()


    @classmethod
    def get_newest_filter_statement(cls, filter:Dict):
        stmt = cls.get_base_select()
        stmt = cls.__set_group_filter(filter, stmt)
        stmt = cls.__set_act_filter(filter, stmt)
        stmt = cls.__set_eq_storename(filter, stmt)
        stmt = cls.__set_itemsort_filter(filter, stmt)
        return stmt

    @classmethod
    def __set_act_filter(cls, filter:Dict, stmt):
        if not fqn.ACT.value in filter.keys() \
            or int(filter[fqn.ACT.value]) == ActFilterName.ALL.id:
            return stmt
        if int(filter[fqn.ACT.value]) == ActFilterName.ACT.id:
            return stmt.where(cls.actcheck.c.act > 0)
        if int(filter[fqn.ACT.value]) == ActFilterName.INACT.id:
            return stmt.where(cls.actcheck.c.act == 0)
        return stmt
    
    @classmethod
    def __set_group_filter(cls, filter:Dict, stmt):
        if not fqn.GID.value in filter.keys() \
            or int(filter[fqn.GID.value]) < 0:
            return stmt
        stmt = (stmt
                .join(GroupItem, GroupItem.item_id == Item.item_id)
                .where(GroupItem.group_id == int(filter[fqn.GID.value]))
                )
        return stmt
    
    @classmethod
    def __set_itemsort_filter(cls, filter:Dict, stmt):
        if not fqn.ISORT.value in filter.keys() \
            or int(filter[fqn.ISORT.value]) < 0:
            return stmt
        fnum = int(filter[fqn.ISORT.value])
        if fnum == ItemSortName.OLD_ITEM.id:
            stmt = (stmt
                    .order_by(Item.item_id.asc())
                    )
            return stmt
        if fnum == ItemSortName.NEW_ITEM.id:
            stmt = (stmt
                    .order_by(Item.item_id.desc())
                    )
            return stmt
        if fnum == ItemSortName.LOW_PRICE.id:
            stmt = (stmt
                    .order_by(NewestItem.newestprice.label("price").asc())
                    )
            return stmt
        if fnum == ItemSortName.HIGH_PRICE.id:
            stmt = (stmt
                    .order_by(NewestItem.newestprice.label("price").desc())
                    )
            return stmt
        if fnum == ItemSortName.ITEM_NAME.id:
            stmt = (stmt
                    .order_by(Item.name.asc())
                    )
            return stmt
        if fnum == ItemSortName.STORE_NAME.id:
            stmt = (stmt
                    .order_by(NewestItem.storename.asc())
                    )
            return stmt
        if fnum == ItemSortName.LOW_TRENDRATE.id:
            stmt = (stmt
                    .order_by(-NewestItem.trendrate.desc())
                    )
            return stmt
        if fnum == ItemSortName.HIGH_TRENDRATE.id:
            stmt = (stmt
                    .order_by(-NewestItem.trendrate.asc())
                    )
            return stmt
        if fnum == ItemSortName.NEW_UPDATE_TIME.id:
            stmt = (stmt
                    .order_by(NewestItem.created_at.desc())
                    )
            return stmt
        return stmt
    
    @classmethod
    def __set_eq_storename(cls, filter:Dict, stmt):
        if not fqn.STORE.value in filter.keys() \
            or int(filter[fqn.STORE.value])  < 0:
            return stmt
        stmt = (stmt
                .join(Store, Store.storename == NewestItem.storename)
                .where(Store.store_id == int(filter[fqn.STORE.value]))
                )
        return stmt
    
    @classmethod
    def add_item(cls,
                 item_name :str,
                 url_path :str,
                 db :Session
                 ):
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
    def __add_newest_data(cls, db :Session, item_id :int):
        ni = NewestItem(
            item_id=item_id,
            newestprice=const_value.INIT_PRICE,
            lowestprice=const_value.INIT_PRICE,
        )
        db.add(ni)
        db.commit()
        db.refresh(ni)
    
    @classmethod
    def update_items_by_dict(cls, db :Session, nidict :Dict) -> None:
        if not 'url_id' in nidict:
            return
        itemids = cls.__get_item_id_from_urlinitem_by_url_id(db, url_id=int(nidict['url_id']))
        if not itemids or len(itemids) == 0:
            return
        for itemid in itemids:
            ni = db.get(NewestItem, itemid)
            if cls.__is_update_item(ni, nidict):
                pi = ParseItemInfo()
                pi.usedPrice = nidict['newestprice']
                pi.oldPrice = ItemQuery.get_most_recent_old_price_of_2days_by_item_id(db, item_id=itemid)
                if not pi.oldPrice:
                    pi.oldPrice = const_value.INIT_PRICE
                nidict["trendrate"] = pi.getTrendRate()
                nidict["lowestprice"] = cls.__get_lowest_price_ever(db,
                                                                    item_id=itemid,
                                                                    newestprice=nidict['newestprice'])
                stmt = (
                    update(NewestItem)
                    .where(NewestItem.item_id == itemid)
                    .values(nidict)
                )
                db.execute(stmt)
        db.commit()
    
    @classmethod
    def __get_lowest_price_ever(cls, db :Session, item_id :int, newestprice :int):
        price = NewestQuery.get_lowest_price_ever(db, item_id=item_id)
        if price == const_value.INIT_PRICE:
            return newestprice
        if newestprice == const_value.INIT_PRICE:
            return price
        if price > newestprice:
            return newestprice
        return price
    
    @staticmethod
    def __is_update_item(ni :NewestItem, nidict :Dict) -> bool:
        if not util.isLocalToday(util.utcTolocaltime(ni.created_at)) \
            or ( ni.newestprice == const_value.INIT_PRICE 
                and int(nidict["newestprice"] != const_value.INIT_PRICE)
                )\
            or ( ni.newestprice > int(nidict["newestprice"])
                and int(nidict["newestprice"] != const_value.INIT_PRICE)
            ):
            return True
        return False

    @classmethod
    def get_item_id_from_urlinitem_by_url_id(cls, db :Session, url_id :int):
        return cls.__get_item_id_from_urlinitem_by_url_id(db, url_id=url_id)

    @classmethod
    def __get_item_id_from_urlinitem_by_url_id(cls, db :Session, url_id :int):
        stmt = (
            select(UrlInItem.item_id)
            .where(UrlInItem.url_id == url_id)
            .group_by(UrlInItem.item_id)
        )
        return db.scalars(stmt).all()
    
    @classmethod
    def get_lowest_price_ever(cls, db :Session, item_id :int):
        stmt = (
            select(NewestItem.lowestprice)
            .where(NewestItem.item_id == item_id)
        )
        return db.scalar(stmt)
    
    @classmethod
    def get_storenames(cls, db :Session) -> List:
        stmt = ( select(NewestItem.storename)
                .group_by(NewestItem.storename)
                )
        return db.execute(stmt).all()
    

class GroupQuery:

    @classmethod
    def add_group(cls, db :Session, name :str) -> int:
        g = Group(groupname=name)
        db.add(g)
        db.commit()
        db.refresh(g)
        return g.group_id

    @classmethod
    def get_all(cls, db :Session):
        return db.scalars(select(Group))
    
    @classmethod
    def get_group_by_name(cls, db :Session, name :str):
        stmt = ( select(Group)
                .where(Group.groupname == name)
                )
        return db.execute(stmt).one_or_none()
    
    @classmethod
    def get_group_by_group_id(cls, db :Session, gid :int):
        stmt = ( select(Group).where(Group.group_id == gid) )
        return db.scalar(stmt)
    
    @classmethod
    def get_group_item_by_group_id(cls, db :Session, group_id :int):
        stmt = ( select(GroupItem)
                .where(GroupItem.group_id == group_id)
                )
        return db.scalars(stmt).all()

    @classmethod
    def update_group_name(cls, db :Session, group_id :int, name :str):
        stmt = ( update(Group)
                .where(Group.group_id == group_id)
                .values(groupname=name)
                )
        db.execute(stmt)
        db.commit()

    @classmethod
    def update_group_item(cls, db :Session, group_id :int, item_list :List[int]):
        current_gilist = cls.get_group_item_by_group_id(db, group_id=group_id)
        current_item_id_list = [gi.item_id for gi in current_gilist]
        
        def __get_del_item_id_list():
            results :List[int] = []
            for item_id in current_item_id_list:
                if not item_id in item_list:
                    results.append(item_id)
            return results
        if len(current_item_id_list) != 0:
            del_item_id_list :List[int] = __get_del_item_id_list()
            cls.__del_group_items(db, group_id=group_id, item_id_list=del_item_id_list)

        def __get_add_item_id_list():
            results :List[int] = []
            for item_id in item_list:
                if not item_id in current_item_id_list:
                    results.append(item_id)
            return results
        add_item_id_list :List[int] = __get_add_item_id_list()
        if len(add_item_id_list) > 0:
            cls.__add_group_items(db, group_id=group_id, item_id_list=add_item_id_list)
        
    
    @classmethod
    def __del_group_items(cls, db :Session, group_id :int, item_id_list :List[int]):
        stmt = ( delete(GroupItem)
                .where(GroupItem.group_id == group_id)
                .where(GroupItem.item_id.in_(item_id_list))
                )
        db.execute(stmt)
        db.commit()
    
    @classmethod
    def __add_group_items(cls, db :Session, group_id :int, item_id_list :List[int]):
        gi_list = [GroupItem(group_id=group_id, item_id=item_id) for item_id in item_id_list]
        db.add_all(gi_list)
        db.commit()
        for gi in gi_list:
            db.refresh(gi)
    
    @classmethod
    def del_group(cls, db :Session, group_id :int):
        cls.__del_group_items_by_group_id(db, group_id)
        stmt = ( delete(Group)
                .where(Group.group_id == group_id)
                )
        db.execute(stmt)
        db.commit()
    
    @classmethod
    def __del_group_items_by_group_id(cls , db :Session, group_id :int):
        stmt = ( delete(GroupItem)
                .where(GroupItem.group_id == group_id)
                )
        db.execute(stmt)
        db.commit()


class ItemQuery:

    @classmethod
    def add(cls,
            db :Session, 
            name :str ="",
            item_id :Optional[int] = None
            ) -> int:
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
        #stmt = insert(Item).values(name=name)
        #res = ses.execute(stmt)
        #ses.commit()
        #return res.inserted_primary_key # taple
    
    @classmethod
    def get_item(cls, db :Session, item_id :int) -> Item:
        stmt = select(Item).where(Item.item_id == item_id)
        return db.scalar(stmt)

    @classmethod
    def get_most_recent_old_price_of_2days_by_item_id(cls, db :Session, item_id :int):
        target_url = (
            select(UrlInItem.url_id)
            .where(UrlInItem.item_id==item_id)
        )
        return cls.__get_most_recent_old_price_of_2days(db, target_url=target_url)
    
    @classmethod
    def get_most_recent_old_price_of_2days_by_url_id(cls, db :Session, url_id :int):
        return cls.__get_most_recent_old_price_of_2days(db, target_url=[url_id])
    

    @classmethod
    def __get_most_recent_old_price_of_2days(cls, db :Session, target_url):
        pricelist = (
            select(PriceLog_2days.created_at,
                   PriceLog_2days.newprice,
                   PriceLog_2days.usedprice,)
            .where(PriceLog_2days.url_id.in_(target_url))
            .where(text_to_boolean(PriceLog_2days.issuccess) == '1')
            .where(utc_to_jst_date_for_query(PriceLog_2days.created_at) <= get_jst_date_for_query(interval_days=INTERVAL_YESTERDAY) )
            .subquery("pricelist")
        )
        return cls.__get_old_min_pricelog(db, price_list_query=pricelist)

    
    @classmethod
    def __get_old_min_pricelog(cls, db :Session, price_list_query):
        pricelist = price_list_query
        max_date = (
            select(
                func.max(
                    utc_to_jst_date_for_query(pricelist.c.created_at)
                    )
                )
                .scalar_subquery()
        )
        lasttime = (
            select(pricelist.c.newprice,
                   pricelist.c.usedprice)
            .where(utc_to_jst_date_for_query(pricelist.c.created_at) == max_date)
            .subquery("lasttime")
        )
        newlowest = (
            select(func.min(lasttime.c.newprice).label("price"))
            .where(lasttime.c.newprice != const_value.INIT_PRICE)
        )
        usedlowest = (
            select(func.min(lasttime.c.usedprice).label("price"))
            .where(lasttime.c.usedprice != const_value.INIT_PRICE)
        )
        lowest = (
            union(newlowest, usedlowest).subquery("lowest")
        )
        stmt = select(func.min(lowest.c.price))
        return db.scalar(stmt)

    @classmethod
    def get_pricelog_2days_by_url_id(cls, db :Session, url_id :int):
        stmt = ( select(PriceLog_2days)
                .where(PriceLog_2days.url_id == url_id)
                )
        res = db.scalars(stmt).all()
        return res

    @classmethod
    def upsert_pricelog(cls, db :Session, pldict :Dict) -> bool:
        if not 'url_id' in pldict:
            return False
        if cls.is_today_pricelog_2days_available(db,
                                                 url_id=pldict['url_id'],
                                                 storename=pldict['storename'],
                                                 usedprice=pldict['usedprice'],
                                                 newprice=pldict['newprice']
                                                ):
            cls.__update_pricelog_2days_by_dict(db, pldict=pldict)
            return True
        cls.__add_pricelog_by_dict(db, pldict=pldict)
        return True
    
    @classmethod
    def is_today_pricelog_2days_available(cls,
                                          db :Session,
                                          url_id :int,
                                          storename :str = "",
                                          usedprice :int = -1 ,
                                          newprice :int = -1) -> bool:
        stmt = (
            select(PriceLog_2days)
            .where(PriceLog_2days.url_id == url_id)
            .where(PriceLog_2days.storename == storename)
            .order_by(PriceLog_2days.created_at.desc())
        )
        pl = db.scalar(stmt)
        if pl:
            if util.isLocalToday(util.utcTolocaltime(pl.created_at))\
                and cls.__is_update_price(insert_used=usedprice,
                                          insert_new=newprice,
                                          db_new=pl.newprice,
                                          db_used=pl.usedprice
                                          ):
                return True
        return False
    
    @classmethod
    def __is_update_price(cls,
                          insert_new :int,
                          insert_used :int,
                          db_new :int,
                          db_used:int):
        if (insert_new != db_new and insert_new != const_value.INIT_PRICE)\
            or (insert_used != db_used and insert_used != const_value.INIT_PRICE):
            return True
        return False

 
    @classmethod
    def update_pricelog_2days_by_dict_and_log_id(cls, db :Session, pldict :Dict, log_id :int):
        stmt = ( update(PriceLog_2days)
                .where(PriceLog_2days.log_id == log_id)
                .values(pldict)
                )
        db.execute(stmt)
        db.commit()

    @classmethod
    def __update_pricelog_2days_by_dict(cls, db :Session, pldict :Dict) -> None:
        url_id = pldict['url_id']
        storename = pldict['storename']
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
        #ses.execute(update_pricelog)
        db.execute(update_pricelog_2dasy)
        db.commit()
    
    @classmethod
    def add_pricelog_2days_by_dict(cls, db :Session, pldict :Dict):
        insert_pricelog_2days = (
            insert(PriceLog_2days)
            .values(pldict)
        )
        db.execute(insert_pricelog_2days)
        db.commit()

    @classmethod
    def __add_pricelog_by_dict(cls, db :Session, pldict :Dict) -> None:
        insert_pricelog = (
            insert(PriceLog)
            .values(pldict)
        )
        insert_pricelog_2days = (
            insert(PriceLog_2days)
            .values(pldict)
        )
        db.execute(insert_pricelog)
        db.execute(insert_pricelog_2days)
        db.commit()

    @classmethod
    def update_items_name_by_item_id(cls, db :Session, item_id :int, name :str) -> None:
        if item_id == const_value.NONE_ID:
            return
        stmt = ( update(Item)
                .where(Item.item_id == item_id)
                .values(name=name)
                )
        db.execute(stmt)
        db.commit()
        
    @classmethod
    def update_items_name_by_url_id(cls, db :Session, url_id :int, uniqname :str) -> None:
        if url_id == const_value.NONE_ID \
            or len(uniqname) == 0:
            return
        itemids = NewestQuery.get_item_id_from_urlinitem_by_url_id(db, url_id=url_id)
        if not itemids or len(itemids) == 0:
            return
        for itemid in itemids:
            iobj = db.get(Item, itemid)
            if iobj and cls.__is_update_items_name(iobj):
                stmt = ( update(Item)
                        .where(Item.item_id == itemid)
                        .values(name=uniqname)
                        )
                db.execute(stmt)
            db.refresh(iobj)
        db.commit()
    
    @classmethod
    def __is_update_items_name(cls, iobj :Item):
        if iobj.name == "":
            return True
        return False
    
    @classmethod
    def get_item_pricelog_by_item_id_1year(cls,
                                           db :Session,
                                           item_id :int,
                                           result_limit :Optional[int] = None
                                           ):
        stmt = (
            select(Item.item_id,
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
            .where(utc_to_jst_datetime_for_query(PriceLog.created_at) >= get_jst_datetime_for_query(interval_years=INTERVAL_ONE_YEARS_AGO))
            .order_by(PriceLog.created_at.desc())
        )
        if result_limit and result_limit > 0:
            stmt = stmt.limit(result_limit)
        return db.execute(stmt).all()

    @classmethod
    def get_daily_min_used_pricelog_by_item_id_and_since_year_ago(cls,
                                                                  db :Session,
                                                                  item_id :int,
                                                                  year :int
                                                                  ):
        stmt = ( select(utc_to_jst_date_for_query(PriceLog.created_at).label("created_at"),
                        func.min(PriceLog.usedprice).label("price")
                        )
                .select_from(PriceLog)
                .join(UrlInItem, UrlInItem.url_id == PriceLog.url_id)
                .where(UrlInItem.item_id == item_id)
                .where(utc_to_jst_datetime_for_query(PriceLog.created_at) >= get_jst_datetime_for_query(interval_years=year*INTERVAL_ONE_YEARS_AGO))
                .where(PriceLog.usedprice > 0)
                .group_by(utc_to_jst_date_for_query(PriceLog.created_at))
        )
        return db.execute(stmt).all()
    
    @classmethod
    def get_daily_min_new_pricelog_by_item_id_and_since_year_ago(cls,
                                                                 db :Session,
                                                                 item_id :int,
                                                                 year :int
                                                                 ):
        stmt = ( select(utc_to_jst_date_for_query(PriceLog.created_at).label("created_at"),
                        func.min(PriceLog.newprice).label("price")
                        )
                .select_from(PriceLog)
                .join(UrlInItem, UrlInItem.url_id == PriceLog.url_id)
                .where(UrlInItem.item_id == item_id)
                .where(utc_to_jst_datetime_for_query(PriceLog.created_at) >= get_jst_datetime_for_query(interval_years=year*INTERVAL_ONE_YEARS_AGO))
                .where(PriceLog.newprice > 0)
                .group_by(utc_to_jst_date_for_query(PriceLog.created_at))
        )
        return db.execute(stmt).all()

    @classmethod
    def get_latest_price_by_item_id_list(cls,
                                         db :Session,
                                         item_id_list :List[int]
                                         ):
        new_price = ( select(Item.name.label('itemname'),
                             PriceLog_2days.storename,
                             PriceLog_2days.newprice.label('price')
                             )
                    .join(UrlInItem, UrlInItem.url_id == PriceLog_2days.url_id)
                    .where(UrlInItem.active == 'True')
                    .where(UrlInItem.item_id.in_(item_id_list))
                    .where(utc_to_jst_date_for_query(PriceLog_2days.created_at) >= get_jst_date_for_query())
                    .where(text_to_boolean(PriceLog_2days.issuccess) == '1')
                    .where(PriceLog_2days.storename != '')
                    .where(PriceLog_2days.newprice > 0)
                    .join(Item, Item.item_id == UrlInItem.item_id)
                )
        used_price = ( select(Item.name.label('itemname'),
                              PriceLog_2days.storename,
                              PriceLog_2days.usedprice.label('price')
                              )
                    .join(UrlInItem, UrlInItem.url_id == PriceLog_2days.url_id)
                    .where(UrlInItem.active == 'True')
                    .where(UrlInItem.item_id.in_(item_id_list))
                    .where(utc_to_jst_date_for_query(PriceLog_2days.created_at) >= get_jst_date_for_query())
                    .where(text_to_boolean(PriceLog_2days.issuccess) == '1')
                    .where(PriceLog_2days.storename != '')
                    .where(PriceLog_2days.usedprice > 0)
                    .join(Item, Item.item_id == UrlInItem.item_id)
                )
        stmt = union(new_price, used_price)
        return db.execute(stmt).all()
    
    @classmethod
    def get_current_storename_list_by_item_id(cls,
                                              db :Session,
                                              item_id_list :List[int]
                                              ):
        stmt = ( select(PriceLog_2days.storename)
                    .join(UrlInItem, UrlInItem.url_id == PriceLog_2days.url_id)
                    .where(UrlInItem.active == 'True')
                    .where(UrlInItem.item_id.in_(item_id_list))
                    .where(utc_to_jst_date_for_query(PriceLog_2days.created_at) >= get_jst_date_for_query())
                    .where(text_to_boolean(PriceLog_2days.issuccess) == '1')
                    .where(PriceLog_2days.storename != '')
                    .group_by(PriceLog_2days.storename)
                )
        #print(stmt)
        return db.execute(stmt).all()

    @classmethod
    def delete_item_relation_by_item_id(cls,
                                        db :Session,
                                        item_id :int
                                        ):
        groupitem_del = ( delete(GroupItem)
                         .where(GroupItem.item_id == item_id)
                         )
        urlinitem_del = ( delete(UrlInItem)
                         .where(UrlInItem.item_id == item_id)
                         )
        newest_del = ( delete(NewestItem)
                      .where(NewestItem.item_id == item_id)
                      )
        item_del = ( delete(Item)
                    .where(Item.item_id == item_id)
                    )
        db.execute(groupitem_del)
        db.execute(urlinitem_del)
        db.execute(newest_del)
        db.execute(item_del)
        db.commit()
    
 
class OrganizerQuery:

    @classmethod
    def get_recent_pricelog_by_url_id(cls,
                                      db :Session,
                                      url_id :int
                                      ):
        sub = ( select(PriceLog)
               .where(PriceLog.url_id == url_id)
               .order_by(PriceLog.created_at.desc())
               .subquery()
               )
        stmt = ( select(sub)
                .group_by(sub.c.storename)
                )
        return db.execute(stmt).all()
    
    @classmethod
    def get_old_pricelog_before_days(cls, db :Session, days :int):
        get_old = ( select(PriceLog)
                   .where(utc_to_jst_datetime_for_query(PriceLog.created_at) <= get_jst_datetime_for_query(interval_days=days*INTERVAL_YESTERDAY))
                   )
        return db.scalars(get_old).all()
    
    @classmethod
    def get_old_pricelog_by_days(cls, db :Session, days :int):
        get_old = ( select(PriceLog)
                   .where(utc_to_jst_date_for_query(PriceLog.created_at) == get_jst_date_for_query(interval_days=days*INTERVAL_YESTERDAY))
                   )
        return db.scalars(get_old).all()
    
    @classmethod
    def get_old_pricelog_2days_by_days(cls, db :Session, days :int):
        get_old = ( select(PriceLog_2days)
                   .where(utc_to_jst_date_for_query(PriceLog_2days.created_at) == get_jst_date_for_query(interval_days=days*INTERVAL_YESTERDAY))
                   )
        return db.scalars(get_old).all()

    
    @classmethod
    def get_pricelog_2days_all(cls, db :Session):
        stmt = select(PriceLog_2days)
        return db.scalars(stmt).all()
    
    @classmethod
    def get_pricelog_2days_today(cls, db :Session):
        stmt = ( select(PriceLog_2days)
                .where(utc_to_jst_date_for_query(PriceLog_2days.created_at) == get_jst_date_for_query())
                )
        return db.scalars(stmt).all()

    @classmethod
    def get_pricelog_today(cls, db :Session):
        stmt = ( select(PriceLog)
                .where(utc_to_jst_date_for_query(PriceLog.created_at) == get_jst_date_for_query())
                )
        return db.scalars(stmt).all()

    @classmethod
    def delete_old_pricelog_before_days(cls, db :Session, days :int):
        delete_old = ( delete(PriceLog)
                      .where(utc_to_jst_datetime_for_query(PriceLog.created_at) <= get_jst_datetime_for_query(interval_days=days*INTERVAL_YESTERDAY))
                      )
        db.execute(delete_old)
        db.commit()

    @classmethod
    def delete_old_pricelog_2days_before_days(cls, db :Session, days :int):
        delete_old = ( delete(PriceLog_2days)
                      .where(utc_to_jst_datetime_for_query(PriceLog_2days.created_at) <= get_jst_datetime_for_query(interval_days=days*INTERVAL_YESTERDAY))
                      )
        db.execute(delete_old)
        db.commit()

    @classmethod
    def delete_pricelog_2days_by_log_id_list(cls, db :Session, log_id_list :List[int]):
        stmt = ( delete(PriceLog_2days)
                .where(PriceLog_2days.log_id.in_(log_id_list))
                )
        db.execute(stmt)
        db.commit()

    @classmethod
    def delete_pricelog_by_log_id_list(cls, db :Session, log_id_list :List[int]):
        stmt = ( delete(PriceLog)
                .where(PriceLog.log_id.in_(log_id_list))
                )
        db.execute(stmt)
        db.commit()
    
    @classmethod
    def add_price_log_by_dict_list(cls, db :Session, pricelog_dict_list :List[Dict]):
        stmt = ( insert(PriceLog)
                .values(pricelog_dict_list)
                )
        db.execute(stmt)
        db.commit()

    @classmethod
    def add_price_log_2days_by_dict_list(cls, db :Session, pricelog_dict_list :List[Dict]):
        stmt = ( insert(PriceLog_2days)
                .values(pricelog_dict_list)
                )
        db.execute(stmt)
        db.commit()

    @classmethod
    def update_pricelog_by_dict_list(cls, db :Session, pricelog_dict_list :List[Dict]):
        for pricelog_dict in pricelog_dict_list:
            log_id = pricelog_dict.pop('log_id', None)
            if log_id is None:
                continue
            stmt = ( update(PriceLog)
                    .where(PriceLog.log_id == log_id)
                    .values(pricelog_dict)
                    )
            db.execute(stmt)
        db.commit()

class OldItemQuery:

    @classmethod
    def add_pricelog_of_old_by_dict_list(cls, db :Session, pricelog_dict_list :List[Dict]):
        stmt = ( insert(PriceLog)
                .values(pricelog_dict_list)
                )
        db.execute(stmt)
        db.commit()
       


class UrlQuery:

    @classmethod
    def add_url(cls, db :Session, urlpath :str) -> int:
        if not urlpath:
            raise RuntimeError
        return cls.__add_url(db, urlpath=urlpath)
    
    @classmethod
    def add_url_and_urlinitem(cls, db :Session, urlpath :str, item_id :Optional[int]=None) -> int:
        if not urlpath:
            raise RuntimeError

        url_id = cls.__add_url(db, urlpath=urlpath)
        if not item_id:
            return url_id
        
        cls.__add_urlinitem(db, url_id=url_id, item_id=item_id)
        return url_id
    
    @classmethod
    def add_urlinitem(cls, db :Session, url_id :int, item_id :int) -> None:
        cls.__add_urlinitem(db, url_id=url_id, item_id=item_id)
    
    @classmethod
    def __add_url(cls, db :Session, urlpath :str) -> int:
        u_obj = cls.get_url(db, urlpath=urlpath)
        if u_obj:
            return u_obj.url_id
        u = Url(urlpath=urlpath)
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.url_id
    
    @classmethod
    def add_urlinitem(cls, db :Session, url_id :int, item_id :int) -> None:
        cls.__add_urlinitem(db, url_id=url_id, item_id=item_id)
    
    @classmethod
    def __add_urlinitem(cls, db :Session, url_id :int, item_id :int) -> None:
        uii_obj = cls.__get_urlinitem(db, url_id=url_id, item_id=item_id)
        if uii_obj:
            return
        uii = UrlInItem(item_id=item_id, url_id=url_id, active=UrlActive.ACTIVE.value)
        db.add(uii)
        db.commit()
        db.refresh(uii)
    
    
    @classmethod
    def update_urlinitem(cls, db :Session, url_id :int, item_id :int, isactive :bool) -> None:
        cls.__update_urlinitem(db, url_id=url_id, item_id=item_id, isactive=isactive)
    
    @classmethod
    def __update_urlinitem(cls, db :Session, url_id :int, item_id :int, isactive :bool) -> None:
        stmt = ( update(UrlInItem)
                .where(UrlInItem.url_id == url_id)
                .where(UrlInItem.item_id == item_id)
                .values(active=str(isactive))
                )
        db.execute(stmt)
        db.commit()

    @classmethod
    def update_url_active(cls, db :Session, item_id :int, url_id :int, isactive :UrlActive) -> None:
        stmt = ( update(UrlInItem)
                .where(UrlInItem.url_id == url_id)
                .where(UrlInItem.item_id == item_id)
                .values(active=isactive.value)
                )
        db.execute(stmt)
        db.commit()
    
    @classmethod
    def update_url_active_all_by_item_id(cls, db :Session, item_id :int, isactive :UrlActive) -> None:
        stmt = ( update(UrlInItem)
                .where(UrlInItem.item_id == item_id)
                .values(active=isactive.value)
                )
        db.execute(stmt)
        db.commit()
    
    @classmethod
    def get_url(cls, db :Session, urlpath :str) -> Url:
        stmt = select(Url).where(Url.urlpath == urlpath)
        return db.scalar(stmt)
    
    @classmethod
    def get_url_all(cls, db :Session):
        stmt = select(Url)
        return db.scalars(stmt)
        
    @classmethod
    def get_urlinitem(cls, db :Session, url_id :int, item_id :int) -> UrlInItem:
        return cls.__get_urlinitem(db, url_id=url_id, item_id=item_id)
    
    @classmethod
    def __get_urlinitem(cls, db :Session, url_id, item_id) -> UrlInItem:
        stmt = ( select(UrlInItem)
                .where(UrlInItem.url_id == url_id)
                .where(UrlInItem.item_id == item_id)
                )
        return db.scalar(stmt)

    @classmethod
    def get_act_items_url(cls, db :Session):
        stmt = ( select(UrlInItem.item_id, Url.urlpath)
                .join(Url, Url.url_id == UrlInItem.url_id, isouter=True)
                .where(UrlInItem.active == UrlActive.ACTIVE.value)
                )
        return db.execute(stmt).all()

    @classmethod
    def get_act_urlinfo_by_item_id(cls, db :Session, item_id :int):
        stmt = ( select(UrlInItem.url_id,
                        Url.urlpath,
                        UrlInItem.active)
                .join(Url, UrlInItem.url_id == Url.url_id)
                .where(UrlInItem.item_id == item_id)
                .where(UrlInItem.active == UrlActive.ACTIVE.value)
                )
        return db.execute(stmt).all()
    
    @classmethod
    def get_urlinfo_by_item_id(cls, db :Session, item_id :int):
        stmt = ( select(UrlInItem.url_id,
                        Url.urlpath,
                        UrlInItem.active)
                .join(Url, UrlInItem.url_id == Url.url_id)
                .where(UrlInItem.item_id == item_id)
                )
        return db.execute(stmt).all()
    
    @classmethod
    def delete_urlinitem(cls, db :Session, item_id :int, url_id :int):
        stmt = ( delete(UrlInItem)
                .where(UrlInItem.item_id == item_id)
                .where(UrlInItem.url_id == url_id)
                )
        db.execute(stmt)
        db.commit()
    

    

    

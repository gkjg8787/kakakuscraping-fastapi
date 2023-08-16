from accessor.item import (
    ItemQuery,
    NewestQuery,
    UrlQuery,
)
from accessor import util as sa_util
from common import util as cm_util
from sqlalchemy import (
    select,
    insert,
    func,
)
from accessor.item.item import OrganizerQuery

from model.item import (
    NewestItem,
    Item,
    UrlInItem,
    PriceLog,
    PriceLog_2days,
)
from .test_db import test_db

def insert_pricelog_sync(db, pldict :dict):
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

def test_get_lowest_price_ever():
    item_id = 7
    val = NewestQuery.get_lowest_price_ever(item_id=item_id)
    assert int(val) == 2211

def test_organizerquery_get_pricelog_2days_today(test_db):
    val = OrganizerQuery.get_pricelog_2days_today()
    assert len(val) == 0

def test_organizerquery_get_pricelog_today(test_db):
    val = OrganizerQuery.get_pricelog_today()
    assert len(val) == 0

def test_isLocalToday(test_db):
    stmt = (select(func.now()) #postgres
            )
    ret = test_db.scalar(stmt)
    assert cm_util.isLocalToday(cm_util.utcTolocaltime(ret))

def test_isLocalToday_alchemy_tolocal(test_db):
    stmt = (select(func.now().op('AT TIME ZONE')('Asia/Tokyo')))
    ret = test_db.scalar(stmt)
    assert cm_util.isLocalToday(ret)

def test_get_newest_created_at(test_db):
    stmt = ( select(Item.name,
                    NewestItem.created_at.op('AT TIME ZONE')('UTC').op('AT TIME ZONE')('Asia/Tokyo'))
            .join(UrlInItem, NewestItem.item_id == UrlInItem.item_id)
            .join(Item, NewestItem.item_id == Item.item_id)
        )
    ret = test_db.execute(stmt).all()
    print(ret)
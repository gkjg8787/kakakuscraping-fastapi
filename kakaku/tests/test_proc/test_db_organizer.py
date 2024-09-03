from datetime import datetime, timezone

from common import const_value
from proc import db_organizer
from model.item import PriceLog, PriceLog_2days

from tests.test_db import test_db


def create_pricelog(
    log_id: int = 1,
    url_id: int = 1,
    created_at: datetime | None = None,
    uniqname: str = "",
    usedprice: int = const_value.INIT_PRICE,
    newprice: int = const_value.INIT_PRICE,
    taxin: str = "1",
    onsale: str = "",
    salename: str = "",
    issuccess: str = "1",
    trendrate: float = 0.0,
    storename: str = "",
):
    if not created_at:
        created_at = datetime.now(timezone.utc)
    return PriceLog(
        log_id=log_id,
        url_id=url_id,
        created_at=created_at,
        uniqname=uniqname,
        usedprice=usedprice,
        newprice=newprice,
        taxin=taxin,
        onsale=onsale,
        salename=salename,
        issuccess=issuccess,
        trendrate=trendrate,
        storename=storename,
    )


def create_pricelog_2days(
    log_id: int = 1,
    url_id: int = 1,
    created_at: datetime | None = None,
    uniqname: str = "",
    usedprice: int = const_value.INIT_PRICE,
    newprice: int = const_value.INIT_PRICE,
    taxin: str = "1",
    onsale: str = "",
    salename: str = "",
    issuccess: str = "1",
    trendrate: float = 0.0,
    storename: str = "",
):
    if not created_at:
        created_at = datetime.now(timezone.utc)
    return PriceLog_2days(
        log_id=log_id,
        url_id=url_id,
        created_at=created_at,
        uniqname=uniqname,
        usedprice=usedprice,
        newprice=newprice,
        taxin=taxin,
        onsale=onsale,
        salename=salename,
        issuccess=issuccess,
        trendrate=trendrate,
        storename=storename,
    )


def test___get_update_for_pricelog_by_2days():
    url_id = 1
    uniqname = "test_item"
    storename = "test_storename"

    today_list = [
        create_pricelog(
            url_id=url_id,
            uniqname=uniqname,
            usedprice=-1,
            newprice=-1,
            issuccess="0",
            storename=storename,
        ),
    ]
    pl_2days_list = [
        create_pricelog_2days(
            url_id=url_id,
            uniqname=uniqname,
            created_at=today_list[0].created_at,
            usedprice=-1,
            newprice=-1,
            issuccess="0",
            storename=storename,
        ),
        create_pricelog_2days(
            url_id=url_id,
            uniqname=uniqname,
            usedprice=5000,
            newprice=-1,
            issuccess="1",
            storename=storename,
        ),
    ]

    ret = db_organizer.__get_update_for_pricelog_by_2days(
        two_days_list=pl_2days_list, pricelog_list=today_list
    )
    assert len(ret["update"]) == 1
    assert len(ret["add"]) == 0

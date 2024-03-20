from sqlalchemy import (
    select,
    func,
)
from common import util
from datetime import datetime, timedelta, timezone
from accessor.read_sqlalchemy import is_sqlite, is_postgre
from tests.test_db import test_db


def test_isLocalToday_by_dbtime(test_db):
    stmt = select(func.now())  # postgres
    ret = test_db.scalar(stmt)
    assert util.isLocalToday(util.utcTolocaltime(ret))


def test_isLocalToday_alchemy_tolocal(test_db):
    if not is_postgre():
        return
    stmt = select(func.now().op("AT TIME ZONE")("Asia/Tokyo"))
    ret = test_db.scalar(stmt)
    assert util.isLocalToday(ret)


def test_is_today_true():
    now = datetime.now(timezone.utc)
    print(f"now={now}")
    assert util.isToday(now)


def test_is_today_false_yesterday():
    yesterday = datetime.now(timezone.utc) - timedelta(1)
    print(f"yesterday={yesterday}")
    assert not util.isToday(yesterday)


def test_is_today_false_2days_ago():
    two_ago = datetime.now(timezone.utc) - timedelta(2)
    print(f"2days_ago={two_ago}")
    assert not util.isToday(two_ago)


def test_is_local_today_true():
    now = util.utcTolocaltime(datetime.now(timezone.utc))
    print(f"now={now}")
    assert util.isLocalToday(now)


def test_is_local_today_false_yesterday():
    yesterday = util.utcTolocaltime(datetime.now(timezone.utc) - timedelta(1))
    print(f"yesterday={yesterday}")
    assert not util.isLocalToday(yesterday)


def test_is_local_today_false_2days_ago():
    two_ago = util.utcTolocaltime(datetime.now(timezone.utc) - timedelta(2))
    print(f"2days_ago={two_ago}")
    assert not util.isLocalToday(two_ago)


def test_is_local_today_datetime():
    now = datetime.now(timezone.utc)
    utcd = datetime(
        now.year,
        now.month,
        now.day,
        now.hour,
        now.minute,
        now.second,
        tzinfo=timezone.utc,
    )
    locd = util.utcTolocaltime(utcd)
    isloc = util.isLocalToday(locd)
    print(f"ori={utcd}, loc={locd}, isloc={isloc}")
    assert isloc

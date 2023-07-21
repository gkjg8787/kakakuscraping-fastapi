from common import util
from datetime import datetime, timedelta


def test_is_today_true():
    now = datetime.utcnow()
    print(f'now={now}')
    assert util.isToday(now)

def test_is_today_false_yesterday():
    yesterday = datetime.utcnow() - timedelta(1)
    print(f'yesterday={yesterday}')
    assert not util.isToday(yesterday)

def test_is_today_false_2days_ago():
    two_ago = datetime.utcnow() - timedelta(2)
    print(f'2days_ago={two_ago}')
    assert not util.isToday(two_ago)

def test_is_local_today_true():
    now = util.utcTolocaltime(datetime.utcnow())
    print(f'now={now}')
    assert util.isLocalToday(now)

def test_is_local_today_false_yesterday():
    yesterday = util.utcTolocaltime(datetime.utcnow() - timedelta(1))
    print(f'yesterday={yesterday}')
    assert not util.isLocalToday(yesterday)

def test_is_local_today_false_2days_ago():
    two_ago = util.utcTolocaltime(datetime.utcnow() - timedelta(2))
    print(f'2days_ago={two_ago}')
    assert not util.isLocalToday(two_ago)

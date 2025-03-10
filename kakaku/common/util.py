from typing import Union
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


JST = ZoneInfo("Asia/Tokyo")


def utcTolocaltime(input_date: datetime):
    if not input_date.tzinfo or input_date.tzinfo != timezone.utc:
        utc_date = input_date.replace(tzinfo=timezone.utc)
    else:
        utc_date = input_date
    return utc_date.astimezone(JST)


def dbtimeTodatetime(dbtime: Union[str, datetime]) -> datetime:
    if type(dbtime) is str:
        return datetime.strptime(dbtime, "%Y-%m-%d %H:%M:%S")
    return dbtime


def isLocalToday(targetlocaltime) -> bool:
    if not targetlocaltime:
        return False
    _targettime = dbtimeTodatetime(targetlocaltime)
    today = utcTolocaltime(datetime.now(timezone.utc)).date()
    if _targettime.date() == today:
        return True
    return False


def isToday(targettime: datetime) -> bool:
    today = datetime.now(timezone.utc).date()
    if targettime.date() == today:
        return True
    return False


def is_num(val: str) -> bool:
    try:
        float(val)
    except ValueError:
        return False
    return True

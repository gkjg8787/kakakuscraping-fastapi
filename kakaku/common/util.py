from typing import Union
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import re

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


url_pattern = re.compile(
    r"^(?:http|ftp)s?://"  # http:// or https:// or ftp:// or ftps://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def is_valid_url(url: str) -> bool:
    if not url:
        return False

    return re.match(url_pattern, url) is not None

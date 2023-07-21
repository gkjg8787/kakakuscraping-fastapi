from typing import Union
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


JST = ZoneInfo('Asia/Tokyo')

def utcTolocaltime(input_date :datetime):
    """Custom filter"""
    utc_date = input_date.replace(tzinfo=timezone.utc)
    return utc_date.astimezone(JST)

def dbtimeTodatetime(dbtime :Union[str,datetime]) -> datetime:
    if type(dbtime) is str:
        return datetime.strptime(dbtime,'%Y-%m-%d %H:%M:%S')
    return dbtime

def isLocalToday(targetlocaltime) -> bool:
    _targettime = dbtimeTodatetime(targetlocaltime)
    today = utcTolocaltime(datetime.utcnow()).date()
    if _targettime.date() == today:
        return True
    return False

def isToday(targettime :datetime) -> bool:
    today = datetime.utcnow().date()
    if targettime.date() == today:
        return True
    return False
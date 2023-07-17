from datetime import datetime, timezone
from zoneinfo import ZoneInfo


JST = ZoneInfo('Asia/Tokyo')

def utcTolocaltime(input_date):
    """Custom filter"""
    utc_date = input_date.replace(tzinfo=timezone.utc)
    return utc_date.astimezone(JST)


def isToday(targettime) -> bool:
    def dbtimeTodatetime(dbtime):
        if type(dbtime) is str:
            return datetime.strptime(dbtime,'%Y-%m-%d %H:%M:%S')
        return dbtime
    _targettime = dbtimeTodatetime(targettime)
    today = utcTolocaltime(datetime.utcnow()).date()
    if _targettime.date() == today:
        return True
    return False
from typing import Union
from sqlalchemy import (
    func,
    schema,
)
from accessor.read_sqlalchemy import (
    is_sqlite,
    is_postgre,
)

INTERVAL_YESTERDAY = -1
INTERVAL_ONE_YEARS_AGO = -1

def utc_to_jst_datetime_for_query(column_datetime :schema.Column):
    if is_sqlite():
        return func.datetime(column_datetime, '+9 hours')
    if is_postgre():
        return column_datetime.op('AT TIME ZONE')('Asia/Tokyo')
    return None

def utc_to_jst_date_for_query(column_datetime :schema.Column):
    if is_sqlite():
        return func.date(column_datetime, '+9 hours')
    if is_postgre():
        return func.date(column_datetime.op('AT TIME ZONE')('Asia/Tokyo'))
    return None

def get_jst_datetime_for_query(interval_days :Union[int,None] = None,
                               interval_years :Union[int,None] = None):
    if is_sqlite():
        jst_base :int = 9
        if interval_days is None:
            ret = func.datetime('now', f'{jst_base} hours')
        else:
            interval_jst = jst_base + interval_days * 24
            ret = func.datetime('now', f'{interval_jst} hours')
        if interval_years is None:
            return ret
        return func.datetime(ret, f'{interval_years} years')
    if is_postgre():
        if interval_days is None:
            ret = func.now().op('AT TIME ZONE')('Asia/Tokyo')
        else:
            ret = func.now().op('AT TIME ZONE')('Asia/Tokyo').op('+')(f'{interval_days} day')
        if interval_years is None:
            return ret
        return ret.op('+')(f'{interval_years} years')
    
def get_jst_date_for_query(interval_days :Union[int,None] = None,
                           interval_years :Union[int,None] = None):
    return func.date(get_jst_datetime_for_query(interval_days=interval_days,
                                                interval_years=interval_years)
                                                )


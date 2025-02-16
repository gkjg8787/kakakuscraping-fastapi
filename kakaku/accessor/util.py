from typing import Union
from sqlalchemy import (
    func,
    schema,
    cast,
    Boolean,
    DECIMAL,
    REAL,
)
import pandas as pd
from accessor.read_sqlalchemy import (
    is_sqlite,
    is_postgre,
)
from accessor.read_sqlalchemy import getEngine

INTERVAL_YESTERDAY = -1
INTERVAL_ONE_YEARS_AGO = -1


def utc_to_jst_datetime_for_query(column_datetime: schema.Column):
    if is_sqlite():
        return func.datetime(column_datetime, "+9 hours")
    if is_postgre():
        return column_datetime.op("AT TIME ZONE")("UTC").op("AT TIME ZONE")(
            "Asia/Tokyo"
        )
    return None


def utc_to_jst_date_for_query(column_datetime: schema.Column):
    return func.date(utc_to_jst_datetime_for_query(column_datetime))


def get_jst_datetime_for_query(
    interval_days: Union[int, None] = None, interval_years: Union[int, None] = None
):
    if is_sqlite():
        jst_base: int = 9
        if interval_days is None:
            ret = func.datetime("now", f"{jst_base} hours")
        else:
            interval_jst = jst_base + interval_days * 24
            ret = func.datetime("now", f"{interval_jst} hours")
        if interval_years is None:
            return ret
        return func.datetime(ret, f"{interval_years} years")
    if is_postgre():
        if interval_days is None:
            ret = func.now().op("AT TIME ZONE")("Asia/Tokyo")
        else:
            ret = (
                func.now()
                .op("AT TIME ZONE")("Asia/Tokyo")
                .op("+")(f"{interval_days} day")
            )
        if interval_years is None:
            return ret
        return ret.op("+")(f"{interval_years} years")
    return None


def get_jst_date_for_query(
    interval_days: Union[int, None] = None, interval_years: Union[int, None] = None
):
    return func.date(
        get_jst_datetime_for_query(
            interval_days=interval_days, interval_years=interval_years
        )
    )


def text_to_boolean(column_bool: schema.Column):
    if is_sqlite():
        return column_bool
    if is_postgre():
        return cast(column_bool, Boolean)
    return None


def text_to_decimal(column_value: schema.Column):
    if is_sqlite():
        return cast(column_value, REAL)
    if is_postgre():
        return cast(column_value, DECIMAL)
    return None


def sqlalchemy_result_all_to_dict_list(result):
    return [dict(row._mapping.items()) for row in result]


def get_dataframe_from_sql(stmt):
    df = pd.read_sql(stmt, getEngine())
    return df

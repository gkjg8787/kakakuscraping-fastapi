import datetime
import dataclasses
from typing import Type
import pandas as pd

from sqlalchemy.orm import Session
from sqlalchemy import (
    select,
    between,
)
from accessor.read_sqlalchemy import getEngine, get_session
from accessor.util import utc_to_jst_date_for_query
from accessor.item import UrlQuery, UrlActive
from model.item import PriceLog, UrlInItem

from ml import MachineLearnModel
from ml.predict_model import (
    MinPriceModel,
    MinPriceModelCommand,
    MinPriceFeatureValueCreatorForPredict,
    MinPriceFeatureValueCreatorCommand,
    PredictionResult,
)
from ml.add_feature_value import (
    has_multiple_season,
    add_week_and_season,
    get_season_column_names,
    get_weekday_column_names,
)
from ml.data_processing_util import shift_multiple_columns
from ml import DataPreProcessing


def get_dataframe_from_sql_by_url_id(
    url_id: int, start: datetime.datetime, end: datetime.datetime | None = None
):
    stmt = (
        select(PriceLog).where(PriceLog.url_id == url_id).where(PriceLog.usedprice > 0)
    )
    start_n = start.replace(tzinfo=None).date()
    if end:
        end_n = end.replace(tzinfo=None).date()
        stmt = stmt.where(
            between(utc_to_jst_date_for_query(PriceLog.created_at), start_n, end_n)
        )
    else:
        stmt = stmt.where(utc_to_jst_date_for_query(PriceLog.created_at) >= start_n)
    df = pd.read_sql(stmt, getEngine())
    return df


def get_dataframe_from_sql_by_item_id_concat_url_log(
    item_id: int, start: datetime.datetime, end: datetime.datetime | None = None
):
    stmt = (
        select(PriceLog)
        .select_from(PriceLog)
        .join(UrlInItem, UrlInItem.url_id == PriceLog.url_id)
        .where(UrlInItem.item_id == item_id)
        .where(UrlInItem.active == UrlActive.ACTIVE.value)
        .where(PriceLog.usedprice > 0)
    )
    start_n = start.replace(tzinfo=None).date()
    if end:
        end_n = end.replace(tzinfo=None).date()
        stmt = stmt.where(
            between(utc_to_jst_date_for_query(PriceLog.created_at), start_n, end_n)
        )
    else:
        stmt = stmt.where(utc_to_jst_date_for_query(PriceLog.created_at) >= start_n)
    df = pd.read_sql(stmt, getEngine())
    return df


class PriceLogPreProcessing(DataPreProcessing):
    df: pd.DataFrame
    has_season: bool = False

    def __init__(self, df: pd.DataFrame):
        self.df, self.has_season = self.data_preprocessing(df=df)

    @classmethod
    def data_preprocessing(self, df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
        new = df.copy()
        new["datetime_column"] = pd.to_datetime(new["created_at"])
        new["date"] = new["datetime_column"].dt.date
        new.drop("datetime_column", axis=1, inplace=True)

        new_date = new.groupby(["date"]).agg(
            {"usedprice": ["max", "min", "mean", "median"]}
        )
        new_date.columns = [
            "max_price",
            "min_price",
            "price_average",
            "price_median",
        ]

        new_date = new_date.reset_index().set_index("date")
        new_date["stores_num"] = new.groupby(["date"])["storename"].nunique()
        new_date = new_date.asfreq("D", method="ffill")

        add_season = has_multiple_season(date_seq=new_date.index)
        new_date = add_week_and_season(
            df=new_date, date_seq=new_date.index, add_season=add_season
        )
        new_date = new_date.rename(columns={"min_price": "y"})
        return new_date, add_season

    def get_dataframe(self) -> pd.DataFrame:
        return self.df


class PriceLogPreProcessingForSARIMAX(DataPreProcessing):
    df: pd.DataFrame

    def __init__(
        self,
        df: pd.DataFrame,
        shift: int,
        shift_column_names: list[str],
        filling_in_missing_value: bool,
    ):
        new_df = df.copy()
        self.df = shift_multiple_columns(
            df=new_df,
            shift=shift,
            shift_columns=shift_column_names,
            filling_in_missing_value=filling_in_missing_value,
        )

    def get_dataframe(self) -> pd.DataFrame:
        return self.df


class PriceLogPreProcessingFactoryEachURL:
    db: any
    item_id: int
    start: datetime.datetime
    end: datetime.datetime | None

    def __init__(
        self,
        item_id: int,
        db: any,
        start: datetime.datetime,
        end: datetime.datetime | None = None,
    ):
        self.db = db
        self.item_id = item_id
        self.start = start
        self.end = end

    def create(self) -> dict[int, PriceLogPreProcessing]:
        ppp_dict = {}
        ret = UrlQuery.get_urlinfo_by_item_id(db=self.db, item_id=self.item_id)
        for r in ret:
            ppp_dict[r.url_id] = PriceLogPreProcessing(
                df=get_dataframe_from_sql_by_url_id(
                    url_id=r.url_id, start=self.start, end=self.end
                )
            )

        return ppp_dict


@dataclasses.dataclass
class MinPricePredictResult:
    start: datetime.datetime
    url_id: int | None = None
    end: datetime.datetime | None = None
    predict_length: int = 1
    mpm: MinPriceModel | None = None
    predict: PredictionResult | None = None


class MinPricePredict:
    shift_column_names = [
        "max_price",
        "price_average",
        "price_median",
        "stores_num",
    ]
    int_value_column_names = [
        "max_price",
        "stores_num",
    ]
    y_column_name = "y"
    ml_model_class: Type[MachineLearnModel]

    def __init__(self, ml_model_class: Type[MachineLearnModel] | None = None):
        if ml_model_class:
            self.ml_model_class = ml_model_class
        else:
            self.ml_model_class = MinPriceModel

    def get_predict_by_item_id(
        self,
        item_id: int,
        start: datetime.datetime,
        end: datetime.datetime | None = None,
        predict_length: int = 14,
        db: Session | None = None,
    ) -> dict[int, MinPricePredictResult]:

        if not db:
            raise ValueError("db is None")
        pppfactory = PriceLogPreProcessingFactoryEachURL(
            item_id=item_id, db=db, start=start, end=end
        )
        ppp_dict = pppfactory.create()
        result_dict = {}
        for url_id, ppp in ppp_dict.items():
            result_dict[url_id] = self.get_minprice_predict(
                url_id=url_id,
                ppp=ppp,
                start=start,
                end=end,
                predict_length=predict_length,
            )
        return result_dict

    def get_predict_by_item_id_concat_url(
        self,
        item_id: int,
        start: datetime.datetime,
        end: datetime.datetime | None = None,
        predict_length: int = 14,
    ):
        df = get_dataframe_from_sql_by_item_id_concat_url_log(
            item_id=item_id, start=start, end=end
        )
        ppp = PriceLogPreProcessing(df=df)
        return self.get_minprice_predict(
            url_id=None, ppp=ppp, start=start, end=end, predict_length=predict_length
        )

    def get_predict_by_url_id(
        self,
        url_id: int,
        start: datetime.datetime,
        end: datetime.datetime | None = None,
        predict_length: int = 14,
    ) -> MinPricePredictResult:
        ppp = PriceLogPreProcessing(
            df=get_dataframe_from_sql_by_url_id(url_id=url_id, start=start, end=end)
        )
        return self.get_minprice_predict(
            url_id=url_id, ppp=ppp, start=start, end=end, predict_length=predict_length
        )

    def get_minprice_predict(
        self,
        url_id: int | None,
        ppp: PriceLogPreProcessing,
        start: datetime.datetime,
        end: datetime.datetime | None = None,
        predict_length: int = 14,
    ):
        pppforsarimax = PriceLogPreProcessingForSARIMAX(
            df=ppp.get_dataframe(),
            shift=1,
            shift_column_names=self.shift_column_names,
            filling_in_missing_value=True,
        )
        mpm = self.ml_model_class()
        mpm.set_data(data=pppforsarimax)

        future_column_names = self.get_future_column_names(has_season=ppp.has_season)
        mpfvccommand = MinPriceFeatureValueCreatorCommand(
            periods=predict_length,
            future_column_names=future_column_names,
            shift_column_names=self.shift_column_names,
            predict_column_names=self.shift_column_names,
            shift=1,
            filling_in_missing_value=True,
            int_value_column_names=self.int_value_column_names,
        )
        mpmcommand = MinPriceModelCommand(
            y_column_name=self.y_column_name,
            exog_column_names=self.get_exog_column_names(
                df=ppp.get_dataframe(), y_column_name=self.y_column_name
            ),
            periods=predict_length,
            fvcreator=MinPriceFeatureValueCreatorForPredict(data=ppp),
            fvcommand=mpfvccommand,
        )
        predict = mpm.get_predict(command=mpmcommand)
        return MinPricePredictResult(
            mpm=mpm,
            predict=predict,
            url_id=url_id,
            start=start,
            end=end,
            predict_length=predict_length,
        )

    def get_future_column_names(self, has_season: bool) -> list[str]:
        ret = get_weekday_column_names().copy()
        if has_season:
            ret += get_season_column_names()
        return ret

    def get_exog_column_names(self, df: pd.DataFrame, y_column_name: str) -> list[str]:
        ret = list(df.columns)
        ret.remove(y_column_name)
        return ret

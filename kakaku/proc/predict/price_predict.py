import datetime
import dataclasses
from typing import Type
from abc import ABC, abstractmethod

import pandas as pd

from sqlalchemy.orm import Session


from accessor.item import UrlQuery
from accessor.item.item import PredictionQuery
from accessor.util import get_dataframe_from_sql

from ml import MachineLearnModel, FeatureValueCreator
from ml.predict_model import (
    MinPriceModel,
    MinPriceModelCommand,
    MinPriceFeatureValueCreatorForPredict,
    MinPriceFeatureValueCreatorCommand,
    TargetColumnFeatureValueCreator,
    TargetColumnFeatureValueCreatorCommand,
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


class PriceLogChartPreProcessing:
    @classmethod
    def data_preprocessing(cls, df: pd.DataFrame) -> tuple[pd.DataFrame]:
        new = df.copy()
        new["datetime_column"] = pd.to_datetime(new["created_at"])
        new["datetime_column"] = (
            new["datetime_column"].dt.tz_localize("UTC").dt.tz_convert("Asia/Tokyo")
        )
        new["date"] = new["datetime_column"].dt.date
        new.drop("datetime_column", axis=1, inplace=True)

        newp = (
            new.loc[(new["newprice"] > 0)]
            .groupby(["date"])
            .agg({"newprice": ["max", "min", "mean", "median"]})
        )
        newp.columns = [
            "new_max",
            "new_min",
            "new_mean",
            "new_median",
        ]
        newp = newp.reset_index().set_index("date")

        usedp = (
            new.loc[(new["usedprice"] > 0)]
            .groupby(["date"])
            .agg(
                {
                    "usedprice": ["max", "min", "mean", "median"],
                }
            )
        )
        usedp.columns = [
            "used_max",
            "used_min",
            "used_mean",
            "used_median",
        ]
        usedp = usedp.reset_index().set_index("date")
        return usedp, newp


class PriceLogPreProcessing(DataPreProcessing):
    df: pd.DataFrame
    has_season: bool = False

    def __init__(
        self,
        df: pd.DataFrame,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
    ):
        self.df, self.has_season = self.data_preprocessing(
            df=df, start_date=start_date, end_date=end_date
        )

    @classmethod
    def data_preprocessing(
        cls,
        df: pd.DataFrame,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
    ) -> tuple[pd.DataFrame, bool]:
        new = df.loc[(df["usedprice"] > 0)].copy()
        new["datetime_column"] = pd.to_datetime(new["created_at"])
        new["datetime_column"] = (
            new["datetime_column"].dt.tz_localize("UTC").dt.tz_convert("Asia/Tokyo")
        )
        if start_date:
            new = new.loc[(new["datetime_column"] >= start_date)]
        if end_date:
            new = new.loc[(new["datetime_column"] <= end_date)]
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
                df=get_dataframe_from_sql(
                    stmt=PredictionQuery.get_stmt_pricelog_by_url_id_and_date_range(
                        url_id=r.url_id, start=self.start, end=self.end
                    )
                )
            )

        return ppp_dict


class CommandFactory(ABC):
    @abstractmethod
    def create(self, *args, **kwargs):
        pass


class FeatureValueCreatorFactory(ABC):
    @abstractmethod
    def create(self, *args, **kwargs):
        pass


class MinPriceFeatureValueCreatorFactory(FeatureValueCreatorFactory):
    def create(
        self,
        ppp: PriceLogPreProcessing,
        periods: int,
        future_column_names: list[str],
        shift_column_names: list[str],
        predict_column_names: list[str],
        int_value_column_names: list[str] = [],
        shift: int = 1,
        filling_in_missing_value: bool = True,
        **kwargs,
    ) -> FeatureValueCreator:
        mpfvccommand = MinPriceFeatureValueCreatorCommand(
            periods=periods,
            future_column_names=future_column_names,
            shift_column_names=shift_column_names,
            predict_column_names=predict_column_names,
            shift=shift,
            filling_in_missing_value=filling_in_missing_value,
            int_value_column_names=int_value_column_names,
        )
        return MinPriceFeatureValueCreatorForPredict(data=ppp, command=mpfvccommand)


class MinPriceModelCommandFactory(CommandFactory):

    def create(
        self,
        periods: int,
        y_column_name: str,
        exog_column_names: list[str],
        fvcreator: FeatureValueCreator,
        **kwargs,
    ) -> MinPriceModelCommand:

        mpmcommand = MinPriceModelCommand(
            y_column_name=y_column_name,
            exog_column_names=exog_column_names,
            periods=periods,
            fvcreator=fvcreator,
        )
        return mpmcommand


class TargetColumnFeatureValueCreatorFactory(FeatureValueCreator):

    def create(
        self,
        ppp: PriceLogPreProcessing,
        y_column_name: str,
        periods: int,
        future_column_names: list[str],
        shift_column_names: list[str],
        predict_column_names: list[str],
        int_value_column_names: list[str] = [],
        lag: int = 1,
        filling_in_missing_value: bool = True,
        **kwargs,
    ):
        command = TargetColumnFeatureValueCreatorCommand(
            periods=periods,
            future_column_names=future_column_names,
            shift_column_names=shift_column_names,
            predict_column_names=predict_column_names,
            lag=lag,
            filling_in_missing_value=filling_in_missing_value,
            drop_today_column=False,
            int_value_column_names=int_value_column_names,
            drop_columns=[y_column_name],
        )
        return TargetColumnFeatureValueCreator(data=ppp, command=command)


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
    fvcreator_factory_class: Type[FeatureValueCreatorFactory]
    ml_model_command_factory_class: Type[CommandFactory]

    def __init__(
        self,
        ml_model_class: Type[MachineLearnModel] | None = None,
        fvcreator_factory_class: Type[FeatureValueCreatorFactory] | None = None,
        ml_model_command_factory_class: Type[FeatureValueCreatorFactory] | None = None,
    ):
        if ml_model_class:
            self.ml_model_class = ml_model_class
        else:
            self.ml_model_class = MinPriceModel

        if fvcreator_factory_class:
            self.fvcreator_factory_class = fvcreator_factory_class
        else:
            self.fvcreator_factory_class = MinPriceFeatureValueCreatorFactory

        if ml_model_command_factory_class:
            self.ml_model_command_factory_class = ml_model_command_factory_class
        else:
            self.ml_model_command_factory_class = MinPriceModelCommandFactory

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
        df: pd.DataFrame,
        start: datetime.datetime,
        end: datetime.datetime | None = None,
        predict_length: int = 14,
    ):
        ppp = PriceLogPreProcessing(df=df, start_date=start, end_date=end)
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
            df=get_dataframe_from_sql(
                stmt=PredictionQuery.get_stmt_pricelog_by_url_id_and_date_range(
                    url_id=url_id, start=start, end=end
                )
            )
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
        fvcreator_param = {
            "ppp": ppp,
            "y_column_name": self.y_column_name,
            "periods": predict_length,
            "future_column_names": future_column_names,
            "shift_column_names": self.shift_column_names,
            "predict_column_names": self.shift_column_names,
            "int_value_column_names": self.int_value_column_names,
            "shift": 1,
            "lag": 1,
            "filling_in_missing_value": True,
        }
        fvcreator = self.fvcreator_factory_class().create(**fvcreator_param)
        mpmcommand = self.ml_model_command_factory_class().create(
            y_column_name=self.y_column_name,
            exog_column_names=self.get_exog_column_names(
                df=ppp.get_dataframe(), y_column_name=self.y_column_name
            ),
            periods=predict_length,
            fvcreator=fvcreator,
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

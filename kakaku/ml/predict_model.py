import dataclasses

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

from .ml import MachineLearnModel, DataPreProcessing, FeatureValueCreator
from .add_feature_value import (
    has_multiple_season,
    add_week_and_season,
    get_weekday_column_names,
    get_season_column_names,
)
from .data_processing_util import shift_multiple_columns, add_multiple_lagged_features


@dataclasses.dataclass
class SARIMAXParam:
    order: tuple = (0, 0, 1)
    seasonal_order: tuple = (0, 0, 0, 7)


@dataclasses.dataclass
class MinPriceFeatureValueCreatorCommand:
    periods: int = 1
    future_column_names: list[str] = dataclasses.field(default_factory=list)
    shift_column_names: list[str] = dataclasses.field(default_factory=list)
    predict_column_names: list[str] = dataclasses.field(default_factory=list)
    shift: int = 1
    filling_in_missing_value: bool = True
    int_value_column_names: list[str] = dataclasses.field(default_factory=list)


class MinPriceFeatureValueCreatorForPredict(FeatureValueCreator):
    base: pd.DataFrame
    command: MinPriceFeatureValueCreatorCommand

    def __init__(
        self, data: DataPreProcessing, command: MinPriceFeatureValueCreatorCommand
    ):
        self.base = data.get_dataframe()
        if not isinstance(self.base.index, pd.DatetimeIndex):
            raise ValueError("index is not DatetimeIndex")
        self.command = command

    def create(
        self,
    ) -> pd.DataFrame:
        command = self.command
        future_df = self.replicate_date_range(
            base=self.base,
            periods=command.periods,
            future_column_names=command.future_column_names,
        ).copy()
        for cname in command.predict_column_names:
            ignore_columns = command.shift_column_names[:]
            ignore_columns.remove(cname)
            new_df = shift_multiple_columns(
                df=self.base.drop(columns=ignore_columns),
                shift=command.shift,
                shift_columns=[cname],
                filling_in_missing_value=command.filling_in_missing_value,
            )
            train_y = new_df[[cname]]
            train_x = new_df.drop(cname, axis=1)

            predict = self.predict_exog_column(
                train_x=train_x,
                train_y=train_y,
                test_x=future_df.drop(columns=command.predict_column_names, axis=1),
            )

            if cname in command.int_value_column_names:
                future_df[cname] = predict.astype(int)
            else:
                future_df[cname] = predict
        return future_df

    @classmethod
    def replicate_date_range(
        cls, base: pd.DataFrame, periods: int, future_column_names: list[str]
    ):
        last_row = base.iloc[[-1]]
        last_date = base.index[-1]
        future_dates = pd.date_range(
            last_date + pd.Timedelta(days=1), periods=periods, freq="D"
        )

        future_df = pd.concat([last_row] * periods)
        future_df.index = future_dates

        future_df.drop(columns=future_column_names, axis=1, inplace=True)

        add_season = has_multiple_season(date_seq=base.index)
        future_df = add_week_and_season(
            df=future_df, date_seq=future_df.index, add_season=add_season
        )

        return future_df

    @classmethod
    def predict_exog_column(
        cls,
        train_x: pd.DataFrame,
        train_y: pd.DataFrame,
        test_x: pd.DataFrame,
    ):
        lr = LinearRegression()
        lr.fit(train_x, train_y)
        return lr.predict(test_x)


@dataclasses.dataclass
class TargetColumnFeatureValueCreatorCommand:
    periods: int = 1
    future_column_names: list[str] = dataclasses.field(default_factory=list)
    shift_column_names: list[str] = dataclasses.field(default_factory=list)
    predict_column_names: list[str] = dataclasses.field(default_factory=list)
    lag: int = 1
    filling_in_missing_value: bool = True
    drop_today_column: bool = False
    int_value_column_names: list[str] = dataclasses.field(default_factory=list)
    drop_columns: list[str] = dataclasses.field(default_factory=list)


class TargetColumnFeatureValueCreator(FeatureValueCreator):
    base: pd.DataFrame
    command: TargetColumnFeatureValueCreatorCommand

    def __init__(
        self, data: DataPreProcessing, command: TargetColumnFeatureValueCreatorCommand
    ):
        self.base = data.get_dataframe()
        if not isinstance(self.base.index, pd.DatetimeIndex):
            raise ValueError("index is not DatetimeIndex")
        self.command = command

    def create(
        self,
    ) -> pd.DataFrame:
        command = self.command
        base = self.base.drop(columns=command.drop_columns, axis=1)
        future_df = self.replicate_date_range(
            base=base,
            periods=command.periods,
            future_column_names=command.future_column_names,
        ).copy()
        for cname in command.predict_column_names:
            ignore_columns = command.shift_column_names[:]
            ignore_columns.remove(cname)
            new_df = add_multiple_lagged_features(
                df=base.drop(columns=ignore_columns, axis=1),
                lag=command.lag,
                column_names=[cname],
                filling_in_missing_value=command.filling_in_missing_value,
                drop_today_column=command.drop_today_column,
            )
            train_y = new_df[[cname]]
            train_x = new_df.drop(cname, axis=1)
            test_x = add_multiple_lagged_features(
                df=future_df.drop(columns=ignore_columns, axis=1),
                lag=command.lag,
                column_names=[cname],
                filling_in_missing_value=command.filling_in_missing_value,
                drop_today_column=True,
            )

            predict = self.predict_exog_column(
                train_x=train_x,
                train_y=train_y,
                test_x=test_x,
            )
            if cname in command.int_value_column_names:
                future_df[cname] = predict.astype(int)
            else:
                future_df[cname] = predict
        return future_df

    @classmethod
    def replicate_date_range(
        cls,
        base: pd.DataFrame,
        periods: int,
        future_column_names: list[str],
    ):
        last_row = base.iloc[[-1]]
        last_date = base.index[-1]
        future_dates = pd.date_range(
            last_date + pd.Timedelta(days=1), periods=periods, freq="D"
        )

        future_df = pd.concat([last_row] * periods)
        future_df.index = future_dates

        future_df.drop(columns=future_column_names, axis=1, inplace=True)

        add_season = has_multiple_season(date_seq=base.index)
        future_df = add_week_and_season(
            df=future_df, date_seq=future_df.index, add_season=add_season
        )

        return future_df

    @classmethod
    def predict_exog_column(
        cls,
        train_x: pd.DataFrame,
        train_y: pd.DataFrame,
        test_x: pd.DataFrame,
    ):
        lr = LinearRegression()
        lr.fit(train_x, train_y)

        lagged_columns = []
        for cname in train_x.columns:
            if "lag" in cname:
                lagged_columns.append(cname)
        if not lagged_columns:
            raise ValueError(f"found not lagged_column in {train_x.columns}")
        if len(lagged_columns) > 1:
            raise ValueError(f"not suppoert multi laggde_columns in {train_x.columns}")

        df = test_x.head(1).copy()
        pre = lr.predict(df)

        def fill_list(base: pd.Series, add_list: list):
            first_value = base.iloc[0]
            new_list = [first_value] + add_list.copy()
            if len(base) > len(new_list):
                new_list.extend(base.tolist()[len(new_list) :])
            return new_list

        next_df = test_x.copy()
        next_df[lagged_columns[0]] = fill_list(
            base=next_df[lagged_columns[0]], add_list=list(pre)
        )

        for i in range(2, len(test_x)):
            pre = lr.predict(next_df[:i])
            next_df[lagged_columns[0]] = fill_list(
                base=next_df[lagged_columns[0]], add_list=list(pre)
            )
        pre = lr.predict(next_df)
        return pre


@dataclasses.dataclass
class PredictionResult:
    predict: any
    index: any
    exog_df: pd.DataFrame | None = None


@dataclasses.dataclass
class MinPriceModelCommand:
    y_column_name: str
    exog_column_names: list[str] = dataclasses.field(default_factory=list)
    periods: int = 1
    fvcreator: FeatureValueCreator | None = None


class MinPriceModel(MachineLearnModel):
    data: pd.DataFrame | None = None
    model: any = None

    def set_data(self, data: DataPreProcessing, model: any = None):
        self.data = data.get_dataframe()
        self.model = model

    def fit(self, y_column_name: str, exog_column_names: list[str] = []):
        train_y, train_x = self.get_training_data(y_column_name)
        param = self.get_param()
        self.model = sm.tsa.SARIMAX(
            train_y.asfreq("D"), exog=train_x.loc[:, exog_column_names], **param
        ).fit()

    def get_predict(
        self,
        command: MinPriceModelCommand,
    ):
        if not self.model:
            self.fit(
                y_column_name=command.y_column_name,
                exog_column_names=command.exog_column_names,
            )

        if not command.fvcreator:
            return PredictionResult(
                predict=self.model.forecast(steps=command.periods),
                index=pd.date_range(
                    self.data.index[-1] + pd.Timedelta(days=1),
                    periods=command.periods,
                    freq="D",
                ),
            )

        future_column_names = get_weekday_column_names().copy()
        if has_multiple_season(date_seq=self.data.index):
            future_column_names += get_season_column_names()

        exog_df = command.fvcreator.create()
        return PredictionResult(
            predict=self.model.forecast(
                steps=command.periods, exog=exog_df.loc[:, command.exog_column_names]
            ),
            index=exog_df.index,
            exog_df=exog_df,
        )

    def get_training_data(self, y_column_name: str, test_size: float | int = 0):
        if test_size == 0:
            train_y = self.data[[y_column_name]]
            train_x = self.data.drop(y_column_name, axis=1)
            return train_y, train_x

        if type(test_size) is float:
            if test_size >= 1.0:
                raise ValueError(f"test_size is too large : {test_size}")
            training_len = int(len(self.data) * (1 - test_size))
        else:
            if test_size > len(self.data):
                raise ValueError(f"test_size is too large : {test_size}")
            training_len = len(self.data) - test_size

        train = self.data.iloc[:training_len]
        train_y = train[[y_column_name]]
        train_x = train.drop(y_column_name, axis=1)
        return train_y, train_x

    def get_param(self) -> dict:
        p = SARIMAXParam()
        return dataclasses.asdict(p)


class PredictionAccuracy:
    mse: float = 0.0
    rmse: float = 0.0
    r2: float = 0.0

    def __init__(self, actual, predict):
        self.mse = mean_squared_error(actual, predict)
        self.rmse = np.sqrt(self.mse)
        self.r2 = r2_score(actual, predict)

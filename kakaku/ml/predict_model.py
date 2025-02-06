import dataclasses

import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression


from .ml import MachineLearnModel, DataPreProcessing
from .add_feature_value import (
    has_multiple_season,
    add_week_and_season,
    get_weekday_column_names,
    get_season_column_names,
)
from .data_processing_util import shift_multiple_columns


@dataclasses.dataclass
class SARIMAXParam:
    order: tuple = (0, 0, 1)
    seasonal_order: tuple = (0, 0, 0, 7)


class FeatureValueCreator:
    def create(self, *args, **kwargs) -> pd.DataFrame:
        return pd.DataFrame()


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

    def __init__(self, data: DataPreProcessing):
        self.base = data.get_dataframe()
        if not isinstance(self.base.index, pd.DatetimeIndex):
            raise ValueError("index is not DatetimeIndex")

    def create(
        self,
        command: MinPriceFeatureValueCreatorCommand,
    ) -> pd.DataFrame:
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
        cls, train_x: pd.DataFrame, train_y: pd.DataFrame, test_x: pd.DataFrame
    ):
        lr = LinearRegression()
        lr.fit(train_x, train_y)
        return lr.predict(test_x)


@dataclasses.dataclass
class PredictionResult:
    predict: any
    index: any


@dataclasses.dataclass
class MinPriceModelCommand:
    y_column_name: str
    exog_column_names: list[str] = dataclasses.field(default_factory=list)
    periods: int = 1
    fvcreator: FeatureValueCreator | None = None
    fvcommand: MinPriceFeatureValueCreatorCommand | None = None


class MinPriceModel(MachineLearnModel):
    data: pd.DataFrame | None = None
    model: any = None

    def set_data(self, data: DataPreProcessing):
        self.data = data.get_dataframe()
        self.model = None

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
            return self.model.forecast(steps=command.periods)

        future_column_names = get_weekday_column_names().copy()
        if has_multiple_season(date_seq=self.data.index):
            future_column_names += get_season_column_names()

        self.valid_fvcommand(command=command)

        exog_df = command.fvcreator.create(command=command.fvcommand)
        return PredictionResult(
            predict=self.model.forecast(
                steps=command.periods, exog=exog_df.loc[:, command.exog_column_names]
            ),
            index=exog_df.index,
        )

    @classmethod
    def valid_fvcommand(cls, command: MinPriceModelCommand):
        fvcommand = command.fvcommand
        if not fvcommand:
            raise ValueError("fvcommand is None")
        if not isinstance(fvcommand, MinPriceFeatureValueCreatorCommand):
            raise ValueError(f"fvcommand is not supported : {type(fvcommand)}")
        if fvcommand.periods != command.periods:
            raise ValueError(
                f"fvcommand.periods({fvcommand.periods}) not equal command.periods({command.periods})"
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

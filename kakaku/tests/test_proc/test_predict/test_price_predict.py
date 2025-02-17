import datetime

import pandas as pd
from pandas import testing as tm

from proc.predict import price_predict
from common.util import dbtimeTodatetime
from ml import MachineLearnModel, DataPreProcessing
from ml.predict_model import (
    MinPriceModelCommand,
    MinPriceFeatureValueCreatorForPredict,
    PredictionResult,
)

from .data_util import create_pricelog_dict


class TestPriceLogChartPreProcessing:
    def test_data_preprocessing(self):
        data = [
            create_pricelog_dict(
                url_id=1,
                created_at=dbtimeTodatetime("2024-01-01 00:00:00"),
                usedprice=1000,
                newprice=-1,
            ),
            create_pricelog_dict(
                url_id=1,
                created_at=dbtimeTodatetime("2024-01-01 10:00:00"),
                usedprice=1600,
                newprice=-1,
            ),
            create_pricelog_dict(
                url_id=1,
                created_at=dbtimeTodatetime("2024-01-02 10:00:00"),
                usedprice=1400,
                newprice=2000,
            ),
            create_pricelog_dict(
                url_id=1,
                created_at=dbtimeTodatetime("2024-01-02 10:00:00"),
                usedprice=1100,
                newprice=3000,
                storename="AAA",
            ),
        ]
        df = pd.DataFrame(data)
        useddf, newdf = price_predict.PriceLogChartPreProcessing.data_preprocessing(
            df=df
        )
        used_corrects = pd.DataFrame(
            {
                "used_max": [1600, 1400],
                "used_min": [1000, 1100],
                "used_mean": [1300.0, 1250.0],
                "used_median": [1300.0, 1250.0],
            },
            index=pd.date_range("2024-01-01", periods=2, freq="D"),
        )
        used_corrects.index = used_corrects.index.date
        new_corrects = pd.DataFrame(
            {
                "new_max": [3000],
                "new_min": [2000],
                "new_mean": [2500.0],
                "new_median": [2500.0],
            },
            index=pd.date_range("2024-01-02", periods=1, freq="D"),
        )
        new_corrects.index = new_corrects.index.date
        tm.assert_frame_equal(useddf, used_corrects[useddf.columns], check_names=False)
        tm.assert_frame_equal(newdf, new_corrects[newdf.columns], check_names=False)


class TestPriceLogPreProcessing:

    def test_data_preprocessing(self):
        data = [
            create_pricelog_dict(
                url_id=1,
                created_at=dbtimeTodatetime("2024-01-01 00:00:00"),
                usedprice=1000,
            ),
            create_pricelog_dict(
                url_id=1,
                created_at=dbtimeTodatetime("2024-01-01 10:00:00"),
                usedprice=1600,
            ),
            create_pricelog_dict(
                url_id=1,
                created_at=dbtimeTodatetime("2024-01-02 10:00:00"),
                usedprice=1400,
            ),
            create_pricelog_dict(
                url_id=1,
                created_at=dbtimeTodatetime("2024-01-02 10:00:00"),
                usedprice=1100,
                storename="AAA",
            ),
        ]
        df = pd.DataFrame(data)
        df, has_season = price_predict.PriceLogPreProcessing.data_preprocessing(df=df)
        assert not has_season
        corrects = pd.DataFrame(
            {
                "y": [1000, 1100],
                "max_price": [1600, 1400],
                "price_average": [1300.0, 1250.0],
                "price_median": [1300.0, 1250.0],
                "stores_num": [1, 2],
                "Monday": [1, 0],
                "Tuesday": [0, 1],
                "Wednesday": [0, 0],
                "Thursday": [0, 0],
                "Friday": [0, 0],
                "Saturday": [0, 0],
                "Sunday": [0, 0],
            },
            index=pd.date_range("2024-01-01", periods=2, freq="D"),
        )
        tm.assert_frame_equal(df, corrects[df.columns], check_names=False)


class MockPriceLogPreProcessing:
    has_season: bool
    df: pd.DataFrame

    def __init__(self):
        self.has_season = False

    def get_dataframe(self) -> pd.DataFrame:
        return self.df


class MockMinPriceModel(MachineLearnModel):
    df: pd.DataFrame
    command: MinPriceModelCommand

    def set_data(self, data: DataPreProcessing, *args, **kawrgs):
        self.df = data.get_dataframe()

    def fit(self, *args, **kwargs):
        pass

    def get_predict(self, *args, **kwargs):
        self.command = kwargs["command"]
        predict = [i for i in range(self.command.periods)]
        return PredictionResult(predict=predict, index=[])


class TestMinPricePredict:

    def test_get_minprice_predict(self, mocker):
        ppp = MockPriceLogPreProcessing()
        ppp.df = pd.DataFrame(
            {
                "y": [1000, 1100],
                "max_price": [1600, 1400],
                "price_average": [1300.0, 1250.0],
                "price_median": [1300.0, 1250.0],
                "stores_num": [1, 2],
                "Monday": [1, 0],
                "Tuesday": [0, 1],
                "Wednesday": [0, 0],
                "Thursday": [0, 0],
                "Friday": [0, 0],
                "Saturday": [0, 0],
                "Sunday": [0, 0],
            },
            index=pd.date_range("2024-01-01", periods=2, freq="D"),
        )
        param = {
            "url_id": 1,
            "ppp": ppp,
            "start": dbtimeTodatetime("2024-01-01 12:00:00"),
            "end": None,
            "predict_length": 14,
        }
        mpp = price_predict.MinPricePredict(ml_model_class=MockMinPriceModel)

        result = mpp.get_minprice_predict(**param)

        assert result.url_id == param["url_id"]
        assert result.start == param["start"]
        assert result.end == param["end"]
        assert len(result.predict.predict) == param["predict_length"]
        assert result.mpm is not None
        mpm = result.mpm
        assert isinstance(mpm, MockMinPriceModel)

        assert isinstance(mpm.command, MinPriceModelCommand)
        assert mpm.command.y_column_name == "y"
        exog_column_names = list(ppp.df.columns)
        exog_column_names.remove("y")
        assert mpm.command.exog_column_names == exog_column_names
        assert mpm.command.periods == param["predict_length"]

        assert isinstance(mpm.command.fvcreator, MinPriceFeatureValueCreatorForPredict)
        tm.assert_frame_equal(mpm.command.fvcreator.base, ppp.get_dataframe())

import datetime

import pandas as pd
from pandas import testing as tm

from proc.predict import price_predict
from common.util import dbtimeTodatetime
from ml import MachineLearnModel, DataPreProcessing
from ml.predict_model import (
    MinPriceModelCommand,
    MinPriceFeatureValueCreatorCommand,
    MinPriceFeatureValueCreatorForPredict,
    PredictionResult,
)
from ml.add_feature_value import (
    get_weekday_column_names,
    get_season_column_names,
)

from tests.test_db import get_test_enging, test_temp_db
from .db_test_data import add_item_url_pricelog_1, add_price_range_1
from .data_util import create_pricelog_dict


def test_get_dataframe_from_sql_by_url_id_start_only(mocker, test_temp_db):
    add_item_url_pricelog_1(test_temp_db)

    mocker.patch("proc.predict.price_predict.getEngine", return_value=get_test_enging())
    param = {
        "url_id": 1,
        "start": dbtimeTodatetime("2024-01-01 12:00:00"),
        "end": None,
    }
    df = price_predict.get_dataframe_from_sql_by_url_id(**param)
    assert len(df) == 1
    assert df["usedprice"].iloc[0] == 1500


def test_get_dataframe_from_sql_by_url_id_start_end(mocker, test_temp_db):
    add_price_range_1(test_temp_db)
    mocker.patch("proc.predict.price_predict.getEngine", return_value=get_test_enging())
    param = {
        "url_id": 1,
        "start": dbtimeTodatetime("2024-01-01 12:00:00"),
        "end": None,
    }
    df = price_predict.get_dataframe_from_sql_by_url_id(**param)
    assert len(df) == 4
    assert df["usedprice"].iloc[0] == 1500
    assert df["usedprice"].iloc[3] == 1600

    param["end"] = dbtimeTodatetime("2024-02-03 00:00:00")
    df = price_predict.get_dataframe_from_sql_by_url_id(**param)
    assert len(df) == 3
    assert df["usedprice"].iloc[2] == 1200


def test_get_dataframe_from_sql_by_item_id_concat_url_log_start_only(
    mocker, test_temp_db
):
    add_item_url_pricelog_1(test_temp_db)
    mocker.patch("proc.predict.price_predict.getEngine", return_value=get_test_enging())
    param = {
        "item_id": 1,
        "start": dbtimeTodatetime("2024-01-01 12:00:00"),
        "end": None,
    }
    df = price_predict.get_dataframe_from_sql_by_item_id_concat_url_log(**param)
    assert len(df) == 2
    assert df["usedprice"].iloc[0] == 1500
    assert df["usedprice"].iloc[1] == 1200


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


class TestPriceLogPreProcessingFactoryEachURL:
    def test_create(self, mocker, test_temp_db):
        add_item_url_pricelog_1(test_temp_db)
        mocker.patch(
            "proc.predict.price_predict.getEngine", return_value=get_test_enging()
        )
        param = {
            "item_id": 1,
            "db": test_temp_db,
            "start": dbtimeTodatetime("2024-01-01 12:00:00"),
            "end": None,
        }
        factory = price_predict.PriceLogPreProcessingFactoryEachURL(**param)
        corrects = {
            1: {
                "usedprice": 1500,
            },
            2: {
                "usedprice": 1200,
            },
        }
        ret = factory.create()
        assert len(ret) == 2
        for url_id, ppp in ret.items():
            df = ppp.get_dataframe()
            assert len(df) == 1
            assert df["y"].iloc[0] == corrects[url_id]["usedprice"]


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
        mpp = price_predict.MinPricePredict(MockMinPriceModel)

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
        assert isinstance(mpm.command.fvcommand, MinPriceFeatureValueCreatorCommand)
        fvcommand = mpm.command.fvcommand
        assert fvcommand.periods == param["predict_length"]
        assert fvcommand.shift == 1
        assert fvcommand.filling_in_missing_value == True
        assert fvcommand.future_column_names == get_weekday_column_names()
        assert set(fvcommand.int_value_column_names) == set(["max_price", "stores_num"])
        shift_column_names = [
            "max_price",
            "price_average",
            "price_median",
            "stores_num",
        ]
        assert set(fvcommand.shift_column_names) == set(shift_column_names)
        assert set(fvcommand.predict_column_names) == set(shift_column_names)

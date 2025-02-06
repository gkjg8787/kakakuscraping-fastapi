import numpy as np
import pandas as pd
from pandas import testing as tm
import pytest

from ml import predict_model
from ml.add_feature_value import (
    get_season_column_names,
    get_weekday_column_names,
    add_week_and_season,
    has_multiple_season,
)
from ml import DataPreProcessing


class MockDataPreProcessing:
    df: pd.DataFrame

    def __init__(self, df):
        self.df = df

    def get_dataframe(self):
        return self.df


class TestMinPriceFeatureValueCreatorForPredict:

    def test_replicate_date_range(self):
        df_dict = {
            "w": [1, 2, 3, 4],
            "z": [10, 20, 30, 40],
        }
        param = {
            "base": pd.DataFrame(
                df_dict,
                index=pd.date_range("20240101", periods=len(df_dict["w"]), freq="D"),
            ),
            "periods": 2,
            "future_column_names": ["w"],
        }
        ret = predict_model.MinPriceFeatureValueCreatorForPredict.replicate_date_range(
            **param
        )
        corrects = pd.DataFrame(
            {"z": [40, 40]},
            index=pd.date_range("20240105", periods=param["periods"], freq="D"),
        )
        new_corrects = add_week_and_season(
            corrects,
            date_seq=corrects.index,
            add_season=has_multiple_season(corrects.index),
        )
        tm.assert_frame_equal(ret, new_corrects)

    def test_create(self, mocker):
        df_dict = {
            "w": [0, 1, 2, 3],
            "y": [10, 20, 30, 40],
            "z": [100, 200, 300, 400],
        }
        df = pd.DataFrame(
            df_dict,
            index=pd.date_range("20240101", periods=len(df_dict["w"]), freq="D"),
        )
        dpp = MockDataPreProcessing(df)
        fvc = predict_model.MinPriceFeatureValueCreatorForPredict(data=dpp)
        param = {
            "periods": 3,
            "future_column_names": ["y"],
            "shift_column_names": ["w", "z"],
            "predict_column_names": ["w", "z"],
            "shift": 1,
            "filling_in_missing_value": True,
            "int_value_column_names": ["z"],
        }
        command = predict_model.MinPriceFeatureValueCreatorCommand(**param)
        correct_predict = pd.Series(
            [40.5, 50.5, 40.6],
            index=pd.date_range("20240105", periods=param["periods"], freq="D"),
        )
        mocker.patch(
            "ml.predict_model.MinPriceFeatureValueCreatorForPredict.predict_exog_column",
            return_value=correct_predict,
        )
        ret = fvc.create(command=command)
        corrects = pd.DataFrame(
            {
                "w": correct_predict.tolist(),
                "z": correct_predict.astype(int).tolist(),
            },
            index=pd.date_range("20240105", periods=param["periods"], freq="D"),
        )
        new_corrects = add_week_and_season(
            corrects,
            date_seq=corrects.index,
            add_season=has_multiple_season(corrects.index),
        )
        tm.assert_frame_equal(ret, new_corrects)

    def test_predict_exog_column(self):
        df_dict = {
            "y": [10, 20, 30, 40, 50],
            "z": [100, 200, 300, 400, 500],
        }
        df = pd.DataFrame(
            df_dict,
            index=pd.date_range("20240101", periods=len(df_dict["y"]), freq="D"),
        )
        target_column_name = "y"
        train_length = 3
        train = df[:train_length]
        test = df[train_length:]
        ret = predict_model.MinPriceFeatureValueCreatorForPredict.predict_exog_column(
            train_x=train.drop(target_column_name, axis=1),
            train_y=train[target_column_name],
            test_x=test.drop(target_column_name, axis=1),
        )
        assert np.allclose(test["y"].to_numpy(), ret)


class TestMinPriceModel:

    def test_get_trainig_data_size_zero(self):
        df_dict = {"y": [1, 2, 3, 4], "z": [10, 20, 30, 40]}
        df = pd.DataFrame(
            df_dict,
            index=pd.date_range("20240101", periods=len(df_dict["y"]), freq="D"),
        )
        target_column_name = "z"
        dpp = MockDataPreProcessing(df=df)
        mpm = predict_model.MinPriceModel()
        mpm.set_data(data=dpp)
        train_y, train_x = mpm.get_training_data(
            y_column_name=target_column_name, test_size=0
        )

        tm.assert_frame_equal(train_x, df.drop(target_column_name, axis=1))
        tm.assert_frame_equal(train_y, df[[target_column_name]])

    def test_get_trainig_data_size_20per(self):
        df_dict = {
            "w": [100, 200, 300, 400, 500],
            "y": [1, 2, 3, 4, 5],
            "z": [10, 20, 30, 40, 50],
        }
        df = pd.DataFrame(
            df_dict,
            index=pd.date_range("20240101", periods=len(df_dict["y"]), freq="D"),
        )
        test_size = 0.2
        train_length = int(len(df) * (1 - test_size))
        target_column_name = "z"
        dpp = MockDataPreProcessing(df=df)
        mpm = predict_model.MinPriceModel()
        mpm.set_data(data=dpp)
        train_y, train_x = mpm.get_training_data(
            y_column_name=target_column_name, test_size=test_size
        )

        tm.assert_frame_equal(
            train_x, df.drop(target_column_name, axis=1)[:train_length]
        )
        tm.assert_frame_equal(train_y, df[[target_column_name]][:train_length])

    def test_get_trainig_data_size_three(self):
        df_dict = {
            "w": [100, 200, 300, 400, 500],
            "y": [1, 2, 3, 4, 5],
            "z": [10, 20, 30, 40, 50],
        }
        df = pd.DataFrame(
            df_dict,
            index=pd.date_range("20240101", periods=len(df_dict["y"]), freq="D"),
        )
        test_size = 3
        train_length = len(df) - test_size
        target_column_name = "z"
        dpp = MockDataPreProcessing(df=df)
        mpm = predict_model.MinPriceModel()
        mpm.set_data(data=dpp)
        train_y, train_x = mpm.get_training_data(
            y_column_name=target_column_name, test_size=test_size
        )

        tm.assert_frame_equal(
            train_x, df.drop(target_column_name, axis=1).iloc[:train_length]
        )
        tm.assert_frame_equal(train_y, df[[target_column_name]].iloc[:train_length])

    def test_valid_fvcommand_no_error(self):
        df_dict = {
            "w": [100, 200, 300, 400, 500],
            "y": [1, 2, 3, 4, 5],
            "z": [10, 20, 30, 40, 50],
        }
        df = pd.DataFrame(
            df_dict,
            index=pd.date_range("20240101", periods=len(df_dict["y"]), freq="D"),
        )
        test_length = 3
        target_column_name = "z"
        exog_column_names = list(df.columns)
        exog_column_names.remove(target_column_name)

        fvcparam = {
            "periods": test_length,
            "future_column_names": [],
            "shift_column_names": [],
            "predict_column_names": [],
            "shift": 1,
            "filling_in_missing_value": True,
            "int_value_column_names": [],
        }
        mpmparam = {
            "y_column_name": target_column_name,
            "exog_column_names": exog_column_names,
            "periods": test_length,
            "fvcreator": None,
            "fvcommand": predict_model.MinPriceFeatureValueCreatorCommand(**fvcparam),
        }
        mpmcommand = predict_model.MinPriceModelCommand(**mpmparam)
        try:
            predict_model.MinPriceModel.valid_fvcommand(command=mpmcommand)
        except ValueError:
            assert False

    def test_valid_fvcommand_no_fvcommand(self):
        mpmparam = {
            "y_column_name": "y",
            "exog_column_names": [],
            "periods": 3,
            "fvcreator": None,
            "fvcommand": None,
        }
        mpmcommand = predict_model.MinPriceModelCommand(**mpmparam)
        with pytest.raises(ValueError):
            predict_model.MinPriceModel.valid_fvcommand(mpmcommand)

    def test_valid_fvcommand_type_not_fvcommand(self):
        mpmparam = {
            "y_column_name": "y",
            "exog_column_names": [],
            "periods": 3,
            "fvcreator": None,
            "fvcommand": list(),
        }
        mpmcommand = predict_model.MinPriceModelCommand(**mpmparam)
        with pytest.raises(ValueError):
            predict_model.MinPriceModel.valid_fvcommand(mpmcommand)

    def test_valid_fvcommand_not_equal_periods(self):
        fvcparam = {
            "periods": 1,
            "future_column_names": [],
            "shift_column_names": [],
            "predict_column_names": [],
            "shift": 1,
            "filling_in_missing_value": True,
            "int_value_column_names": [],
        }
        mpmparam = {
            "y_column_name": "y",
            "exog_column_names": [],
            "periods": 2,
            "fvcreator": None,
            "fvcommand": predict_model.MinPriceFeatureValueCreatorCommand(**fvcparam),
        }
        mpmcommand = predict_model.MinPriceModelCommand(**mpmparam)
        with pytest.raises(ValueError):
            predict_model.MinPriceModel.valid_fvcommand(mpmcommand)

    def test_fit(self):
        df_dict = {
            "w": [100, 200, 300, 400, 500],
            "y": [1, 2, 3, 4, 5],
            "z": [10, 20, 30, 40, 50],
        }
        df = pd.DataFrame(
            df_dict,
            index=pd.date_range("20240101", periods=len(df_dict["y"]), freq="D"),
        )
        test_length = 3
        target_column_name = "z"
        exog_column_names = list(df.columns)
        exog_column_names.remove(target_column_name)

        fvcparam = {
            "periods": test_length,
            "future_column_names": [],
            "shift_column_names": [],
            "predict_column_names": [],
            "shift": 1,
            "filling_in_missing_value": True,
            "int_value_column_names": [],
        }
        mpmparam = {
            "y_column_name": target_column_name,
            "exog_column_names": exog_column_names,
            "periods": test_length,
            "fvcreator": None,
            "fvcommand": predict_model.MinPriceFeatureValueCreatorCommand(**fvcparam),
        }
        mpmcommand = predict_model.MinPriceModelCommand(**mpmparam)
        mpm = predict_model.MinPriceModel()
        dpp = MockDataPreProcessing(df=df)
        mpm.set_data(data=dpp)
        assert mpm.model is None
        mpm.fit(
            y_column_name=mpmparam["y_column_name"],
            exog_column_names=mpmparam["exog_column_names"],
        )
        assert mpm.model is not None

    def test_get_predict(self):
        df_dict = {
            "w": [100, 200, 300, 400, 500],
            "y": [1, 2, 3, 4, 5],
            "z": [10, 20, 30, 40, 50],
        }
        df = pd.DataFrame(
            df_dict,
            index=pd.date_range("20240101", periods=len(df_dict["y"]), freq="D"),
        )
        test_length = 3
        target_column_name = "y"
        exog_column_names = list(df.columns)
        exog_column_names.remove(target_column_name)
        future_column_names = get_weekday_column_names().copy()
        add_season = has_multiple_season(date_seq=df.index)
        shift_column_names = ["w", "z"]
        df = add_week_and_season(df=df, date_seq=df.index, add_season=add_season)
        dpp = MockDataPreProcessing(df=df)

        fvcparam = {
            "periods": test_length,
            "future_column_names": future_column_names,
            "shift_column_names": shift_column_names,
            "predict_column_names": shift_column_names,
            "shift": 1,
            "filling_in_missing_value": True,
            "int_value_column_names": [],
        }
        fvcreator = predict_model.MinPriceFeatureValueCreatorForPredict(data=dpp)
        mpmparam = {
            "y_column_name": target_column_name,
            "exog_column_names": exog_column_names,
            "periods": test_length,
            "fvcreator": fvcreator,
            "fvcommand": predict_model.MinPriceFeatureValueCreatorCommand(**fvcparam),
        }
        mpmcommand = predict_model.MinPriceModelCommand(**mpmparam)

        mpm = predict_model.MinPriceModel()
        mpm.set_data(data=dpp)
        ret = mpm.get_predict(command=mpmcommand)
        assert len(ret.predict) == test_length
        assert np.all((ret.predict >= 1) & (ret.predict <= 5))
        tm.assert_index_equal(
            ret.index,
            pd.date_range(
                df.index[-1] + pd.Timedelta(days=1), periods=test_length, freq="D"
            ),
        )

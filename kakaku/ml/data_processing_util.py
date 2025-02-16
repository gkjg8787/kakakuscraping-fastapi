import pandas as pd
import numpy as np


def shift_multiple_columns(
    df: pd.DataFrame,
    shift: int = 0,
    shift_columns: list[str] = [],
    filling_in_missing_value: bool = False,
) -> pd.DataFrame:
    """
    DataFrameの複数のカラムの値に対して行をずらす関数。

    Args:
        df: 入力DataFrame
        shift: shift_columnsで指定したカラムを指定したintの数だけindexをずらします。正がindex後ろ、負がindex前にずらします。
        shift_columns: ずらしたいカラム名のリスト。
        filling_in_missing_value: Trueの場合、shiftでずらした分の欠損値をshift>0なら後の日付の値、shift<0なら前の日付の値で埋めます。Falseなら何もしません。

    Returns:
        指定したカラムの値がshift分ずらされた新しいDataFrame。
        指定されたカラムが存在しない場合はValueErrorを発生させる。
    """
    ret = df.copy()
    if not shift or not shift_columns:
        return ret

    for col in shift_columns:
        if col not in ret.columns:
            raise ValueError(f"not found {col} in {ret.columns}")

    if filling_in_missing_value:
        if shift > 0:
            ret[shift_columns] = ret[shift_columns].shift(shift).bfill()
        else:
            ret[shift_columns] = ret[shift_columns].shift(shift).ffill()
    else:
        ret[shift_columns] = ret[shift_columns].shift(shift)
    return ret


def add_multiple_lagged_features(
    df: pd.DataFrame,
    lag: int,
    column_names: list[str],
    filling_in_missing_value: bool = False,
    drop_today_column: bool = False,
) -> pd.DataFrame:
    """
    DataFrameの複数のカラムに対して複数のlagged featureを追加する関数。

    Args:
        df: 入力DataFrame。
        lag: ラグの値 (正の整数)。
        column_names: ラグを適用するカラム名のリスト。
        filling_in_missing_value: Trueなら欠損値を埋める。Falseなら何もしない。
        drop_today_column: Trueなら当日のラグ適用したカラムを削除。

    Returns:
        lagged featureが追加された新しいDataFrame。
        入力がDataFrameでない場合、
        lagが正の整数でない場合、指定されたカラムが存在しない場合はValueErrorを発生させる。
    """

    if not isinstance(df, pd.DataFrame):
        raise ValueError("df type is not pandas.DataFrame")

    if not isinstance(lag, int) or lag <= 0:
        raise ValueError("lag type is not int")

    if not isinstance(column_names, list):
        raise ValueError("column_names type is not list")

    for col in column_names:
        if col not in df.columns:
            raise ValueError(f"not found '{col}' ")

    df_lagged = df.copy()

    new_column_names = []
    for column_name in column_names:
        for i in range(1, lag + 1):
            df_lagged[f"{column_name}_lag{i}"] = df[column_name].shift(i)
            new_column_names.append(f"{column_name}_lag{i}")

    if drop_today_column:
        df_lagged.drop(columns=column_names, inplace=True)

    if filling_in_missing_value:
        df_lagged[new_column_names] = df_lagged[new_column_names].bfill()

    return df_lagged


def create_sequences(
    data: pd.DataFrame | pd.Series | np.ndarray,
    timesteps: int,
    y_column_index: int,
    x_includes_y: bool = True,
):
    """
    渡されたデータをx,yに分け、xをtimesteps毎にまとめる。

    Args:
        data: 入力DataFrame, Series, numpy配列のどれか。
        timesteps: いくつずつxにまとめるかの数。
        y_column_index: 目的のカラムのインデックス番号。
        x_includes_y: 目的のカラムをxに含めるか。

    Returns:
        x,y timesteps数毎にまとめたxとyのnumpy配列
    """
    xs = []
    ys = []
    if isinstance(data, pd.DataFrame) or isinstance(data, pd.Series):
        np_data = np.array(data)
    else:
        np_data = data
    if not x_includes_y:
        target_index = np.arange(0, np_data.shape[1])
        target_index = np.delete(target_index, y_column_index)

    for i in range(len(np_data) - timesteps):
        if x_includes_y:
            xs.append(np_data[i : (i + timesteps)])
        else:
            xs.append(np_data[i : (i + timesteps), target_index])
        ys.append(np_data[i + timesteps, y_column_index])

    return np.array(xs), np.array(ys)


def create_sequences_multi_step(
    data: pd.DataFrame | pd.Series | np.ndarray,
    timesteps: int,
    y_column_index: int,
    x_includes_y: bool = True,
    n_outputs: int = 1,
):
    """
    渡されたデータをx,yに分け、xをtimesteps分毎にまとめ、yをn_outputs分毎にまとめる。

    Args:
        data: 入力DataFrame, Series, numpy配列のどれか。
        timesteps: いくつずつxにまとめるかの数。
        y_column_index: 目的のカラムのインデックス番号。
        x_includes_y: 目的のカラムをxに含めるか。
        n_outputs: 目的カラムをいくつずつまとめるかの数。

    Returns:
        x,y timesteps数毎にまとめたxとn_outpus数毎まとめたyのnumpy配列
    """
    xs = []
    ys = []
    if isinstance(data, pd.DataFrame) or isinstance(data, pd.Series):
        np_data = np.array(data)
    else:
        np_data = data
    if not x_includes_y:
        target_index = np.arange(0, np_data.shape[1])
        target_index = np.delete(target_index, y_column_index)

    for i in range(len(np_data) - timesteps - n_outputs + 1):
        if x_includes_y:
            xs.append(np_data[i : (i + timesteps)])
        else:
            xs.append(np_data[i : (i + timesteps), target_index])
        ys.append(np_data[i + timesteps : i + timesteps + n_outputs, y_column_index])
    return np.array(xs), np.array(ys)

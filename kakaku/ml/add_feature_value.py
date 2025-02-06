import pandas as pd


def has_multiple_season(date_seq: pd.DataFrame | pd.Index) -> bool:
    def get_season(dt):
        month = dt.month
        if 3 <= month <= 5:
            return "spring"
        elif 6 <= month <= 8:
            return "summer"
        elif 9 <= month <= 11:
            return "autumn"
        else:
            return "winter"

    season = pd.to_datetime(date_seq).map(get_season)
    if season.nunique() > 1:
        return True

    return False


def get_weekday_column_names():
    weekdays = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    return weekdays


def get_season_column_names():
    seasons = ["spring", "summer", "autumn", "winter"]
    return seasons


def add_week_and_season(
    df: pd.DataFrame, date_seq: pd.DataFrame | pd.Index, add_season: bool = True
) -> pd.DataFrame:
    future_df = df.copy()

    weekdays = get_weekday_column_names()

    future_df["date"] = pd.to_datetime(date_seq)
    future_df["week"] = future_df["date"].dt.day_name()

    future_df["week"] = pd.Categorical(
        future_df["week"], categories=weekdays, ordered=False
    )

    future_df = pd.get_dummies(
        future_df, columns=["week"], prefix="", prefix_sep="", dtype=int
    )

    if not add_season:
        future_df.drop("date", axis=1, inplace=True)
        return future_df

    future_df["summer"] = (
        future_df["date"].apply(lambda x: x.month in [6, 7, 8]).astype(int)
    )
    future_df["autumn"] = (
        future_df["date"].apply(lambda x: x.month in [9, 10, 11]).astype(int)
    )
    future_df["winter"] = (
        future_df["date"].apply(lambda x: x.month in [12, 1, 2]).astype(int)
    )
    future_df["spring"] = (
        future_df["date"].apply(lambda x: x.month in [3, 4, 5]).astype(int)
    )
    future_df.drop("date", axis=1, inplace=True)
    return future_df


def create_predict_dataframe(
    base: pd.DataFrame, predict: list | pd.Series, predict_column_name: str
) -> pd.DataFrame:

    future_periods = len(predict)

    last_date = base.index[-1]
    future_dates = pd.date_range(
        last_date + pd.Timedelta(days=1), periods=future_periods, freq="D"
    )

    if isinstance(predict, list):
        future_df = pd.DataFrame({predict_column_name: predict}, index=future_dates)
    elif isinstance(predict, pd.Series):
        future_df = pd.DataFrame(
            {predict_column_name: predict.tolist()}, index=future_dates
        )
    else:
        raise ValueError(f"predict is not support type : {type(predict)}")

    future_df = add_week_and_season(future_df, date_seq=future_df.index)
    return future_df


def create_new_dateindex(df: pd.DataFrame, periods: int) -> pd.DataFrame:

    last_date = df.index[-1]
    next_day = last_date + pd.Timedelta(days=1)
    additional_dates = pd.date_range(next_day, periods=periods, freq="D")

    additional_data = pd.DataFrame(index=additional_dates)
    additional_data = add_week_and_season(
        additional_data, date_seq=additional_data.index
    )

    df_extended = pd.concat([df, additional_data])

    return df_extended

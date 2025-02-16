import pandas as pd

from common.util import dbtimeTodatetime

from accessor.item.item import PredictionQuery

from tests.test_db import test_temp_db, get_test_enging
from .db_test_data import add_item_url_pricelog_1, add_price_range_1


class TestPredictionQuery:
    @classmethod
    def get_dataframe_from_sql(cls, stmt):
        df = pd.read_sql(stmt, get_test_enging())
        return df

    def test_get_dataframe_from_sql_by_url_id_start_only(self, test_temp_db):
        add_item_url_pricelog_1(test_temp_db)

        param = {
            "url_id": 1,
            "start": dbtimeTodatetime("2024-01-01 12:00:00"),
            "end": None,
        }
        df = self.get_dataframe_from_sql(
            stmt=PredictionQuery.get_stmt_pricelog_by_url_id_and_date_range(**param)
        )
        assert len(df) == 1
        assert df["usedprice"].iloc[0] == 1500

    def test_get_dataframe_from_sql_by_url_id_start_end(self, test_temp_db):
        add_price_range_1(test_temp_db)
        param = {
            "url_id": 1,
            "start": dbtimeTodatetime("2024-01-01 12:00:00"),
            "end": None,
        }
        df = self.get_dataframe_from_sql(
            stmt=PredictionQuery.get_stmt_pricelog_by_url_id_and_date_range(**param)
        )
        assert len(df) == 4
        assert df["usedprice"].iloc[0] == 1500
        assert df["usedprice"].iloc[3] == 1600

        param["end"] = dbtimeTodatetime("2024-02-03 00:00:00")
        df = self.get_dataframe_from_sql(
            stmt=PredictionQuery.get_stmt_pricelog_by_url_id_and_date_range(**param)
        )
        assert len(df) == 3
        assert df["usedprice"].iloc[2] == 1200

    def test_get_dataframe_from_sql_by_item_id_concat_url_log_start_only(
        self, test_temp_db
    ):
        add_item_url_pricelog_1(test_temp_db)

        param = {
            "item_id": 1,
            "start": dbtimeTodatetime("2024-01-01 12:00:00"),
            "end": None,
        }
        df = self.get_dataframe_from_sql(
            stmt=PredictionQuery.get_stmt_pricelog_by_item_id_and_date_range(**param)
        )
        assert len(df) == 2
        assert df["usedprice"].iloc[0] == 1500
        assert df["usedprice"].iloc[1] == 1200

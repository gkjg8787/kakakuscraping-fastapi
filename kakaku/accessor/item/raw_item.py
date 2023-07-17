from typing import Dict

from sqlalchemy import text
from sqlalchemy.orm import Session

from accessor.read_sqlalchemy import getEngine
   
class NewestQuery:
    W_ALL_ITEMQ = """
        WITH act_t AS (
  SELECT
    item_id
    ,COUNT(url_id) AS act
  FROM
    siteupdate
  WHERE
    active="True"
  GROUP BY
    item_id
),
inact_t AS (
  SELECT
    su.item_id
    ,0 AS act
  FROM
    siteupdate AS su
  WHERE
    su.item_id NOT IN
      (
        SELECT
          item_id
        FROM
          act_t
      )
  GROUP BY
    su.item_id
),
actcheck AS (
  SELECT * FROM act_t
UNION ALL
  SELECT * FROM inact_t
)
    """
    W_ALL_SEL_PART ="""
SELECT
  i.item_id
  ,i.name
  ,ni.url_id
  ,url.urlpath
  ,datetime(ni.created_at,"localtime") AS created_at
  ,ni.newestprice AS price
  ,ni.salename
  ,ni.trendrate
  ,ni.storename
  ,ni.lowestprice
  ,actc.act
    """
    W_ALL_FROM_PART = """
        FROM
  items AS i
    LEFT OUTER JOIN newestitem AS ni
      ON i.item_id = ni.item_id
    LEFT OUTER JOIN url
      ON ni.url_id = url.url_id
    LEFT OUTER JOIN actcheck AS actc
      ON i.item_id = actc.item_id
    """
    BASEQ = W_ALL_ITEMQ + W_ALL_SEL_PART + W_ALL_FROM_PART
    WHERE_ACT = ' WHERE actc.act > 0'
    ACTQ = BASEQ + WHERE_ACT
    @classmethod
    def get_newest_data(cls, filter:Dict):
        engine = getEngine()
        ses = Session(engine)
        return ses.execute(text(cls.ACTQ)).all()
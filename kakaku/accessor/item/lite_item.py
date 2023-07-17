import sqlite3
from typing import Dict
from common import read_config

dbconf = read_config.get_databases()

from . import raw_item

class NewestQuery:

    @classmethod
    def get_newest_data(cls, filter:Dict):
        conn = sqlite3.connect(dbconf['default']['database'])
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute(raw_item.NewestQuery.ACTQ)
        retobj = cur.fetchall()
        conn.close()
        if retobj is None:
                    return ()
        return retobj

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
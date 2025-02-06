import datetime
from common.util import dbtimeTodatetime


def create_pricelog_dict(
    url_id: int,
    created_at: datetime.datetime | None = None,
    uniqname: str = "test_item",
    usedprice: int = -1,
    newprice: int = -1,
    taxin: bool = True,
    onsale: bool = False,
    salename: str = "",
    issuccess: bool = True,
    trendrate: float = 0.0,
    storename: str = "駿河屋",
):
    if not created_at:
        created_at = dbtimeTodatetime("2024-01-01 10:00:00")
    ret = {
        "url_id": url_id,
        "created_at": created_at,
        "uniqname": uniqname,
        "usedprice": usedprice,
        "newprice": newprice,
        "taxin": taxin,
        "onsale": onsale,
        "salename": salename,
        "issuccess": issuccess,
        "trendrate": trendrate,
        "storename": storename,
    }
    return ret

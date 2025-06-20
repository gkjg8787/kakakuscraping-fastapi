import os
from datetime import datetime, timezone
from html_parser import netoff_html_parse

detail_fpath = os.path.dirname(__file__) + "/data/netoff_detail.html"


def test_netoff_parse():
    correct = {
        "url_id": 1,
        "uniqname": "Xenoblade Definitive Edition",
        "usedprice": 4998,
        "newprice": -1,
        "taxin": True,
        "onsale": False,
        "salename": "",
        "issuccess": True,
        "oldprice": -1,
        "trendrate": 0,
        "url": "https://www.netoff.co.jp/detail/0013104313/",
        "storename": "ネットオフ",
        "created_at": datetime(2025, 6, 20, 13, 30, tzinfo=timezone.utc),
    }
    with open(detail_fpath, "r") as fp:
        np = netoff_html_parse.NetoffParse(
            fp, id=correct["url_id"], date=correct["created_at"], url=correct["url"]
        )
        for item in np.getItems():
            for key, val in item.getOrderedDict().items():
                assert val == correct[key]

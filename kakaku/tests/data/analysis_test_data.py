from datetime import datetime, timedelta

SURUGAYA = "駿河屋"
SURUGAYA_CHIBA = "駿河屋千葉中央店"
NETOFF = "ネットオフ"
BOOKOFF = "ブックオフ"
GEO = "ゲオ"


class ResultItem:
    _mapping: dict

    def __init__(self, result: dict = {}):
        self._mapping = result


one_week_ago = datetime.utcnow() + timedelta(days=-7)
three_days_ago = datetime.utcnow() + timedelta(days=-3)
one_days_ago = datetime.utcnow() + timedelta(days=-1)
now = datetime.utcnow()


def id4_2days_set(date1: datetime, date2: datetime):
    data = [
        {
            "item_id": 1,
            "url_id": 1,
            "active": "True",
            "newprice": -1,
            "usedprice": 1500,
            "storename": SURUGAYA,
            "created_at": date1,
        },
        {
            "item_id": 2,
            "url_id": 2,
            "active": "True",
            "newprice": -1,
            "usedprice": 1200,
            "storename": SURUGAYA,
            "created_at": date1,
        },
        {
            "item_id": 2,
            "url_id": 2,
            "active": "True",
            "newprice": -1,
            "usedprice": 1600,
            "storename": SURUGAYA_CHIBA,
            "created_at": date1,
        },
        {
            "item_id": 3,
            "url_id": 3,
            "active": "True",
            "newprice": -1,
            "usedprice": 3000,
            "storename": BOOKOFF,
            "created_at": date1,
        },
        {
            "item_id": 4,
            "url_id": 4,
            "active": "True",
            "newprice": -1,
            "usedprice": 3300,
            "storename": NETOFF,
            "created_at": date1,
        },
        {
            "item_id": 1,
            "url_id": 1,
            "active": "True",
            "newprice": -1,
            "usedprice": 1400,
            "storename": SURUGAYA,
            "created_at": date2,
        },
        {
            "item_id": 2,
            "url_id": 2,
            "active": "True",
            "newprice": -1,
            "usedprice": 1200,
            "storename": SURUGAYA,
            "created_at": date2,
        },
        {
            "item_id": 2,
            "url_id": 2,
            "active": "True",
            "newprice": -1,
            "usedprice": 1600,
            "storename": SURUGAYA_CHIBA,
            "created_at": date2,
        },
        {
            "item_id": 3,
            "url_id": 3,
            "active": "True",
            "newprice": -1,
            "usedprice": 3000,
            "storename": BOOKOFF,
            "created_at": date2,
        },
        {
            "item_id": 4,
            "url_id": 4,
            "active": "True",
            "newprice": -1,
            "usedprice": 3300,
            "storename": NETOFF,
            "created_at": date2,
        },
    ]
    return data


def id4_3days_set(date1: datetime, date2: datetime, date3: datetime):
    data = [
        {
            "item_id": 1,
            "url_id": 1,
            "active": "True",
            "newprice": -1,
            "usedprice": 1500,
            "storename": SURUGAYA,
            "created_at": date1,
        },
        {
            "item_id": 2,
            "url_id": 2,
            "active": "True",
            "newprice": -1,
            "usedprice": 1200,
            "storename": SURUGAYA,
            "created_at": date1,
        },
        {
            "item_id": 2,
            "url_id": 2,
            "active": "True",
            "newprice": -1,
            "usedprice": 1600,
            "storename": SURUGAYA_CHIBA,
            "created_at": date1,
        },
        {
            "item_id": 3,
            "url_id": 3,
            "active": "True",
            "newprice": -1,
            "usedprice": 3000,
            "storename": BOOKOFF,
            "created_at": date1,
        },
        {
            "item_id": 4,
            "url_id": 4,
            "active": "True",
            "newprice": -1,
            "usedprice": 3300,
            "storename": NETOFF,
            "created_at": date1,
        },
        {
            "item_id": 1,
            "url_id": 1,
            "active": "True",
            "newprice": -1,
            "usedprice": 1400,
            "storename": SURUGAYA,
            "created_at": date2,
        },
        {
            "item_id": 2,
            "url_id": 2,
            "active": "True",
            "newprice": -1,
            "usedprice": 1200,
            "storename": SURUGAYA,
            "created_at": date2,
        },
        {
            "item_id": 2,
            "url_id": 2,
            "active": "True",
            "newprice": -1,
            "usedprice": 1600,
            "storename": SURUGAYA_CHIBA,
            "created_at": date2,
        },
        {
            "item_id": 3,
            "url_id": 3,
            "active": "True",
            "newprice": -1,
            "usedprice": 3000,
            "storename": BOOKOFF,
            "created_at": date2,
        },
        {
            "item_id": 4,
            "url_id": 4,
            "active": "True",
            "newprice": -1,
            "usedprice": 3300,
            "storename": NETOFF,
            "created_at": date2,
        },
        {
            "item_id": 1,
            "url_id": 1,
            "active": "True",
            "newprice": -1,
            "usedprice": 1400,
            "storename": SURUGAYA,
            "created_at": date3,
        },
        {
            "item_id": 2,
            "url_id": 2,
            "active": "True",
            "newprice": -1,
            "usedprice": 1000,
            "storename": SURUGAYA,
            "created_at": date3,
        },
        {
            "item_id": 2,
            "url_id": 2,
            "active": "True",
            "newprice": -1,
            "usedprice": 1600,
            "storename": SURUGAYA_CHIBA,
            "created_at": date3,
        },
        {
            "item_id": 3,
            "url_id": 3,
            "active": "True",
            "newprice": -1,
            "usedprice": 3300,
            "storename": BOOKOFF,
            "created_at": date3,
        },
        {
            "item_id": 4,
            "url_id": 4,
            "active": "True",
            "newprice": -1,
            "usedprice": 3600,
            "storename": NETOFF,
            "created_at": date3,
        },
    ]
    return data


def get_one_week_dict():
    return id4_3days_set(one_week_ago, three_days_ago, now)


def get_one_week_data():
    one_week: list[dict] = get_one_week_dict()
    res: list[ResultItem] = []
    for one in one_week:
        res.append(ResultItem(one))
    return res


def get_two_days_dict():
    return id4_2days_set(one_days_ago, now)


def get_two_days_data():
    two_day: list[dict] = get_two_days_dict()
    res: list[ResultItem] = []
    for one in two_day:
        res.append(ResultItem(one))
    return res

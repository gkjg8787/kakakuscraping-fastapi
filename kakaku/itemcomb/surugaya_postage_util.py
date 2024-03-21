import argparse
import json
import time
import re

from common import const_value
from itemcomb.surugaya_postage import create_posdb
from itemcomb.surugaya_postage import post_surugaya_postage
from itemcomb.prefecture import PrefectureName

from accessor.read_sqlalchemy import Session, get_session

MIN_POST_WAIT_TIME = 0.5


class PrefecturePostage:
    name: str = ""
    national_fee: int | None = None
    local_fee: int | None = None

    def get_postage(self):
        if self.local_fee:
            return self.local_fee
        else:
            return self.national_fee

    def is_national_fee(self):
        return self.local_fee is None


class StoreShippingInfo:
    shop_name: str = ""
    url: str = ""
    shop_id: int
    prefectures_postage: list[PrefecturePostage]

    def __init__(self, res: dict):
        self.prefectures_postage = []
        if "shop_name" in res:
            self.shop_name = res["shop_name"]
        if "url" in res:
            self.url = res["url"]
        if "shop_id" in res:
            self.shop_id = int(res["shop_id"])
        if "postage" in res:
            self.set_postages(res["postage"])

    def set_postages(self, postages):
        if not postages:
            return
        for p in postages:
            prefpos = PrefecturePostage()
            if "national_fee" in p and p["national_fee"]:
                prefpos.national_fee = int(p["national_fee"])
            if "fee" in p and p["fee"]:
                prefpos.local_fee = int(p["fee"])
            if "prefecture" in p:
                prefpos.name = p["prefecture"]
            if not prefpos.name:
                if "warning" not in p or "list_pref_fee not exist" not in p["warning"]:
                    continue
                prefpos.name = PrefectureName.get_country_wide_name()

            self.prefectures_postage.append(prefpos)

    def get_prefecture_postage(self, prefecture: str):
        if not self.prefectures_postage:
            return None
        if (
            len(self.prefectures_postage) == 1
            and self.prefectures_postage[0].name
            == PrefectureName.get_country_wide_name()
        ):
            return self.prefectures_postage[0].get_postage()

        for prefpos in self.prefectures_postage:
            if prefpos.name == prefecture:
                return prefpos.get_postage()
        return None


class ShippingResult:
    shipping_list: list[StoreShippingInfo] = []

    def __init__(self, result: dict):
        self.shipping_list = list()
        if "result" in result:
            for r in result["result"]:
                ssi = StoreShippingInfo(r)
                self.shipping_list.append(ssi)

    def get_list(self):
        return self.shipping_list


def get_shippingResult(
    db: Session,
    storename: str,
    prefectures: list[str] | None = None,
    post_wait_time: float = MIN_POST_WAIT_TIME,
    exact: bool = False,
):
    ret = funcstart(
        db=db,
        storename=storename,
        exact=exact,
        post_wait_time=post_wait_time,
        prefectures=prefectures,
    )
    return ShippingResult(ret)


def convert_storename_to_search_storename(storename: str):
    ret = storename.replace("駿河屋", "")
    ret = ret.replace("ブックマーケット", "")
    ret = re.sub(r"\s+", "", ret)
    ret.strip()
    m = re.findall(r"(.+)店", ret)
    if not m:
        return ret
    if m[0]:
        return m[0]
    return ret


def outputResult(rdict, outputtype):
    if outputtype == "json":
        print(json.dumps(rdict, ensure_ascii=False))
        return
    for shoppos in rdict["result"]:
        print(f"-------{shoppos['shop_name']}:{shoppos['shop_id']}-------")
        print(f"{shoppos}")
        print("---------------------------------")


def getPostage(db: Session, pdict: dict, wait_time: float = MIN_POST_WAIT_TIME):
    # print(pdict)
    if not pdict["exact"]:
        gsl = create_posdb.grepShopList(db, name=pdict["storename"])
    else:
        shopid = create_posdb.getShopID(db, name=pdict["storename"])
        if shopid == const_value.NONE_ID:
            gsl = []
        else:
            gsl = [{"shop_name": pdict["storename"], "shop_id": shopid}]
    reslist = []
    for shop in gsl:
        resdic = {}
        jdicts = post_surugaya_postage.getPrefecturePostage(
            shop["shop_id"], pdict["pref"]
        )
        resdic.update(shop)
        resdic["postage"] = jdicts
        reslist.append(resdic)
        if wait_time < MIN_POST_WAIT_TIME:
            wait_time = MIN_POST_WAIT_TIME
        time.sleep(wait_time)
    return {"result": reslist}


def checkUpdateShopList(db: Session, forced_shop_update, without_shop_update):
    if not create_posdb.is_todays_data_dailyonlineshopinfo(db=db):
        create_posdb.create_dailyonlineshopinfo(db=db)
        return
    if without_shop_update:
        return
    if forced_shop_update or create_posdb.is_expired_dailyonlineshopinfo(db=db):
        create_posdb.create_dailyonlineshopinfo(db=db)
        return


def getPrefList():
    return PrefectureName.get_all_prefecturename()


def inPrefList(prefs):
    pl = getPrefList()
    for p in prefs:
        if p not in pl:
            return False
    return True


def parseParamOpt(param):
    parser = argparse.ArgumentParser(
        description="get Shipping fee for Surugaya Marketplace"
    )
    parser.add_argument("storename", metavar="name", help="store name", type=str)
    parser.add_argument("-x", "--exact", help="exact match", action="store_true")
    shopupdate = parser.add_mutually_exclusive_group()
    shopupdate.add_argument(
        "-su",
        "--shop-update",
        dest="forced_shop_update",
        help="forced shoplist update",
        action="store_true",
        default=False,
    )
    shopupdate.add_argument(
        "-nsu",
        "--no-shop-update",
        dest="without_shop_update",
        help="without shoplist update",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-ot",
        "--outputtype",
        metavar="type",
        help="Set output format",
        choices=["text", "json"],
        default="json",
        type=str,
    )
    parser.add_argument(
        "-p",
        "--pref",
        metavar="prefucture",
        help="prefecture to it is sent",
        default=["東京都"],
        type=str,
        nargs="*",
    )

    args = parser.parse_args(param)
    # print(args)
    res = {"storename": ""}
    if args.storename is not None and len(args.storename) > 0:
        res["storename"] = args.storename
    else:
        print("parameter ng")
        return

    res["exact"] = args.exact
    res["forced_shop_update"] = args.forced_shop_update
    res["without_shop_update"] = args.without_shop_update
    res["outputtype"] = args.outputtype

    if args.pref is not None and len(args.pref) > 0:
        if inPrefList(args.pref):
            res["pref"] = args.pref
        else:
            print("pref parameter ng")
            return

    return res


def funcstart(
    db: Session,
    storename: str,
    exact: bool,
    post_wait_time: float,
    forced_shop_update: bool = False,
    without_shop_update: bool = False,
    outtype: str = "dict",
    prefectures: list[str] = ["東京都"],
):
    checkUpdateShopList(db, forced_shop_update, without_shop_update)
    rdict = getPostage(
        db,
        pdict={
            "storename": storename,
            "exact": exact,
            "pref": prefectures,
        },
        wait_time=post_wait_time,
    )
    if outtype == "dict":
        return rdict
    else:
        return json.dumps(rdict, ensure_ascii=False)


def cmdstart(argv):
    pdict = parseParamOpt(argv[1:])
    # print(pdict)
    with next(get_session()) as db:
        checkUpdateShopList(
            db, pdict["forced_shop_update"], pdict["without_shop_update"]
        )
        rdict = getPostage(db, pdict)
    outputResult(rdict, pdict["outputtype"])

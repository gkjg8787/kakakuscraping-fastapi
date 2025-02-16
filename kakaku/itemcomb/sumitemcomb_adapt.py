import os
import json
from typing import List
from pathlib import Path
import subprocess
import time

from sqlalchemy.orm import Session

from itemcomb import sumitemcomb

from accessor.item import (
    ItemQuery,
)
from accessor.store import StoreQuery

from common.read_config import (
    get_exec_itemcomb,
    get_srcdir,
    get_itemcomb_price_margin,
)
from common import cmnlog

SUMITEMCOMB_BINARY = "Go-ItemCombSum"
EXEC_BIN_TYPE = "bin"


def getBoundaryInDict(d):
    BOUNDARY = "boundary"
    if BOUNDARY not in d or d[BOUNDARY] is None:
        return "0<="
    return d[BOUNDARY]


def getPostageInDict(d):
    POSTAGE = "postage"
    if POSTAGE not in d or d[POSTAGE] is None:
        return "0"
    return d[POSTAGE]


def createStoreConf(db: Session, itemidlist: List[int]):
    res = ItemQuery.get_current_storename_list_by_item_id(db, item_id_list=itemidlist)
    if res is None or len(res) == 0:
        return {}
    storenames: List[str] = [t for r in res for t in r]
    sp = StoreQuery.get_storepostage_by_storename(db, storenames=storenames)
    dicl = [dict(row._mapping.items()) for row in sp]
    storeconf = {}
    for d in dicl:
        if d["storename"] not in storeconf:
            storeconf[d["storename"]] = list()
        vald = {}
        vald["boundary"] = getBoundaryInDict(d)
        vald["postage"] = getPostageInDict(d)
        storeconf[d["storename"]].append(vald)
    return storeconf


def deleteLogger():
    logname = cmnlog.LogName.ITEMCOMB
    return cmnlog.deleteLogger(logname)


def getLogger():
    logname = cmnlog.LogName.ITEMCOMB
    return cmnlog.getLogger(logname)


def get_filename():
    return os.path.basename(__file__)


def convert_result_of_proc(result: dict):
    newret = {}
    for k, v in result.items():
        if k == "errormsg" and len(v) > 0:
            newret["errmsg"] = v
            continue
        if k == "sumposin":
            newret["sum_pos_in"] = v
            continue
        if k == "sumpostage":
            newret["sum_postage"] = v
            continue
        if k == "storesums":
            for storesum in v:
                indic = {}
                indic["items"] = storesum["items"]
                indic["postage"] = storesum["postage"]
                indic["sum_pos_out"] = storesum["sumposout"]
                newret[storesum["storename"]] = indic
            continue
    return newret


def storeconfToStrStoreConf(storeconf: dict):
    for stl in storeconf.values():
        for t in stl:
            for k, v in t.items():
                if "postage" == k:
                    t[k] = str(v)
    return storeconf


def get_command_options() -> list[str]:
    conf = get_itemcomb_price_margin()
    result: list[str] = []
    if "type" not in conf:
        return []
    if "fix" == conf["type"]:
        result.extend(["--margin-type", "fix"])
        if "value" in conf and int(conf["value"]) >= 0:
            result.extend(["--margin-value", f'{conf["value"]}'])
    elif "rate" == conf["type"]:
        result.extend(["--margin-type", "rate"])
        if "value" in conf and float(conf["value"]) >= 0:
            result.extend(["--margin-value", f'{conf["value"]}'])
        if "min-value" in conf and int(conf["min-value"]) >= 0:
            result.extend(["--min-margin", f'{conf["min-value"]}'])
    return result


def call_searchcomb(storeconf: dict, itemlist: list[dict]):
    return sumitemcomb.searchcomb(
        sumitemcomb.SearchcombCommand(
            storeconf=storeconf,
            itemlist=itemlist,
            options=sumitemcomb.PriceComparitionMargin(get_itemcomb_price_margin()),
        )
    )


def start_searchcomb_subprocess(storeconf: dict, itemlist: list[dict]):
    base_path = str(get_srcdir())
    logger = getLogger()
    cmd = str(Path(base_path, SUMITEMCOMB_BINARY))
    if not os.path.isfile(cmd):
        logger.warning(f"not exist cmd={cmd}")
        return call_searchcomb(storeconf=storeconf, itemlist=itemlist)

    strstconf = storeconfToStrStoreConf(storeconf)
    cmdline = [cmd, json.dumps(strstconf), json.dumps(itemlist)]
    cmdopts = get_command_options()
    cmdline.extend(cmdopts)
    p = subprocess.run(
        cmdline,
        encoding="utf-8",
        capture_output=True,
    )
    logger.debug(f"{get_filename()} returncode={p.returncode}, stdout={str(p.stdout)}")
    ret = json.loads(str(p.stdout).rstrip())
    if len(ret) > 0:
        return convert_result_of_proc(ret)
    return {}


def start_searchcomb(storeconf: dict, itemlist: list[dict], exec_type: str):
    if str(exec_type).lower() != EXEC_BIN_TYPE.lower():
        return call_searchcomb(storeconf=storeconf, itemlist=itemlist)
    else:
        return start_searchcomb_subprocess(storeconf, itemlist)


def startCalcSumitemComb(db: Session, itemidlist: List[int]):
    res = ItemQuery.get_latest_price_by_item_id_list(db, item_id_list=itemidlist)
    itemlist = [dict(row._mapping.items()) for row in res]
    storeconf = createStoreConf(db, itemidlist=itemidlist)

    logger = getLogger()
    logger.info(f"{get_filename()} searchcomb start")
    logger.info(f"{get_filename()} storeconf= {storeconf}")
    logger.info(f"{get_filename()} itemlist= {itemlist}")
    logger.info(f"{get_filename()} exec= {get_exec_itemcomb()}")
    stime = time.perf_counter()
    ret = start_searchcomb(storeconf, itemlist, get_exec_itemcomb())
    etime = time.perf_counter()
    ret["proc_time"] = etime - stime
    logger.info(get_filename() + " searchcomb end")
    return ret

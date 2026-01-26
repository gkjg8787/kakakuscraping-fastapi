import os
from enum import Enum, auto
import argparse
from functools import wraps
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from common import cmnlog, const_value
from accessor.item.item import OldItemQuery, OrganizerQuery
from accessor.server import OrganizeLogQuery
from accessor.read_sqlalchemy import get_session, get_old_db_session
from model.item import PriceLog_2days, PriceLog


# 古いDBへ移動する条件の経過日数
DAYS_TO_MOVE_OLD_DATA = 730

# pricelog_2daysがurl_id,storename毎に直近の古いデータ数の上限(本日から-2日分は2つ以上でも可)
MAX_LOG_2DAYS_DATA_CNT = 2


class DBOrganizerCmd(Enum):
    ALL = auto()
    PRICELOG_CLEANER = auto()
    PRICELOG_2DAYS_CLEANER = auto()
    SYNC_PRICELOG = auto()


class FuncStatus(Enum):
    START = auto()
    END = auto()


def get_filename():
    return os.path.basename(__file__)


def getLogger():
    return cmnlog.getLogger(cmnlog.LogName.DB_ORGANIZE)


def output_func_db_log(db: Session, name: DBOrganizerCmd, status: FuncStatus):
    OrganizeLogQuery.add_log(db, name=name.name, status=status.name)


def start_end_db_log(name):
    def _start_end_db_log(func):
        @wraps(func)
        def wrapper(*args, **kargs):
            if "db" in kargs:
                output_func_db_log(kargs["db"], name, FuncStatus.START)
            result = func(*args, **kargs)
            if "db" in kargs:
                output_func_db_log(kargs["db"], name, FuncStatus.END)
            return result

        return wrapper

    return _start_end_db_log


@start_end_db_log(DBOrganizerCmd.SYNC_PRICELOG)
def sync_2days_to_pricelog_today(db: Session):
    today_2days_update_list = OrganizerQuery.get_pricelog_2days_today(db)
    log = getLogger()
    if len(today_2days_update_list) == 0:
        log.info(f"{get_filename()} sync_2days_to_pricelog_today no update")
        return

    today_pricelog_list = OrganizerQuery.get_pricelog_today(db)
    if len(today_pricelog_list) == 0:
        add_dict_list: list[dict] = []
        for p in today_2days_update_list:
            dic = p.toDict()
            dic.pop("log_id")
            add_dict_list.append(dic)
        log.info(
            get_filename()
            + f" sync_2days_to_pricelog_today add length={len(add_dict_list)}"
        )
        # log.info(get_filename() + f"{add_dict_list}")
        log.info(f"{get_filename()} sync_2days_to_pricelog_today add start")
        OrganizerQuery.add_price_log_by_dict_list(db, pricelog_dict_list=add_dict_list)
        log.info(f"{get_filename()} sync_2days_to_pricelog_today add end")
        return

    results = __get_update_for_pricelog_by_2days(
        two_days_list=today_2days_update_list, pricelog_list=today_pricelog_list
    )

    if len(results["update"]) > 0:
        log.info(
            get_filename()
            + f" sync_2days_to_pricelog_today update length={len(results['update'])}"
        )
        # log.info(get_filename() + f"{results['update']}")
        log.info(f"{get_filename()} sync_2days_to_pricelog_today update start")
        OrganizerQuery.update_pricelog_by_dict_list(
            db, pricelog_dict_list=results["update"]
        )
        log.info(f"{get_filename()} sync_2days_to_pricelog_today update end")
    if len(results["add"]) > 0:
        log.info(
            get_filename()
            + f" sync_2days_to_pricelog_today add length={len(results['add'])}"
        )
        log.info(f"{get_filename()} sync_2days_to_pricelog_today add start")
        # log.info(get_filename() + f"{results['add']}")
        OrganizerQuery.add_price_log_by_dict_list(db, pricelog_dict_list=results["add"])
        log.info(f"{get_filename()} sync_2days_to_pricelog_today add end")
    return


def __get_update_for_pricelog_by_2days(
    two_days_list: list[PriceLog_2days], pricelog_list: list[PriceLog]
):
    update_dict_list: list = []
    add_dict_list: list = []

    def is_update(two: PriceLog_2days, pricelog: PriceLog):
        if two.created_at < pricelog.created_at:
            return False
        if two.url_id != pricelog.url_id or two.storename != pricelog.storename:
            return False
        if two.newprice == pricelog.newprice and two.usedprice == pricelog.usedprice:
            return False
        if (
            pricelog.newprice == const_value.INIT_PRICE
            and two.newprice != const_value.INIT_PRICE
            and pricelog.usedprice == two.usedprice
        ):
            return True
        if (
            pricelog.usedprice == const_value.INIT_PRICE
            and two.usedprice != const_value.INIT_PRICE
            and pricelog.newprice == two.newprice
        ):
            return True
        return False

    def eq_log(two: PriceLog_2days, pricelog: PriceLog):
        return two.compare_self_to_pricelog(pricelog)

    for two in two_days_list:
        exist_log = False
        for pricelog in pricelog_list:
            if is_update(two=two, pricelog=pricelog):
                dic = two.toDict()
                dic["log_id"] = pricelog.log_id
                update_dict_list.append(dic)
                # print(f"two={two}, pricelog={pricelog}")
                exist_log = True
                continue
            if eq_log(two=two, pricelog=pricelog):
                exist_log = True
                continue
        if not exist_log:
            dic = two.toDict()
            dic.pop("log_id")
            add_dict_list.append(dic)

    return {"update": update_dict_list, "add": add_dict_list}


@start_end_db_log(DBOrganizerCmd.PRICELOG_CLEANER)
def pricelog_cleaner(db: Session):
    old_list = OrganizerQuery.get_old_pricelog_before_days(
        db, days=DAYS_TO_MOVE_OLD_DATA
    )
    move_list: list[dict] = []
    for old in old_list:
        move_list.append(old.toDict())
    if len(move_list) > 0:
        log = getLogger()
        log.info(f"{get_filename()} pricelog_cleaner move length={len(move_list)}")
        log.info(f"{get_filename()} pricelog_cleaner move start")
        old_db = next(get_old_db_session())
        OldItemQuery.add_pricelog_of_old_by_dict_list(
            old_db, pricelog_dict_list=move_list
        )
        log.info(f"{get_filename()} pricelog_cleaner move end")
    OrganizerQuery.delete_old_pricelog_before_days(db, days=DAYS_TO_MOVE_OLD_DATA)


@start_end_db_log(DBOrganizerCmd.PRICELOG_2DAYS_CLEANER)
def pricelog_2days_cleaner(db: Session):
    OrganizerQuery.delete_old_pricelog_2days_before_days(db, days=DAYS_TO_MOVE_OLD_DATA)

    pricelog_result = OrganizerQuery.get_pricelog_2days_all(db)
    delete_pricelog_list = __get_delete_pricelog_2days_list(pricelog_result)
    # print(f"delete_list_len={len(delete_pricelog_list)}")
    if len(delete_pricelog_list) > 0:
        log = getLogger()
        log.info(
            get_filename()
            + f" pricelog_2days_cleaner delete length={len(delete_pricelog_list)}"
        )
        delete_log_id_list = [v.log_id for v in delete_pricelog_list]
        log.info(f"{get_filename()} pricelog_2days_cleaner delete start")
        OrganizerQuery.delete_pricelog_2days_by_log_id_list(
            db, log_id_list=delete_log_id_list
        )
        log.info(f"{get_filename()} pricelog_2days_cleaner delete end")


def __get_delete_pricelog_2days_list(pricelog_result: list[PriceLog_2days]):
    pricelog_dict: dict[str, list[PriceLog_2days]] = {}
    delete_pricelog_list: list[PriceLog_2days] = []

    for r in pricelog_result:
        key = str(r.url_id) + ":" + r.storename
        if key in pricelog_dict:
            pricelog_dict[key].append(r)
        else:
            pricelog_dict[key] = [r]

    for k in pricelog_dict.keys():
        if len(pricelog_dict[k]) > MAX_LOG_2DAYS_DATA_CNT:
            delete_target: list[PriceLog_2days] = []
            yesterday = datetime.now(timezone.utc) - timedelta(1)
            for pricelog in pricelog_dict[k]:
                if pricelog.created_at.date() >= yesterday.date():
                    continue
                else:
                    delete_target.append(pricelog)
                continue
            delete_max = len(pricelog_dict[k]) - MAX_LOG_2DAYS_DATA_CNT
            if delete_max <= 0:
                continue
            for idx, pricelog in enumerate(delete_target):
                old = __get_old_pricelog_2days(delete_target[idx:])
                if old is None:
                    continue
                delete_pricelog_list.append(old)
                if delete_max <= len(delete_pricelog_list):
                    break
                continue

    return delete_pricelog_list


def __get_old_pricelog_2days(pricelog_list: list[PriceLog_2days]):
    old = None
    for pricelog in pricelog_list:
        if not old:
            old = pricelog
            continue
        if old.created_at > pricelog.created_at:
            old = pricelog
    return old


def param_parser(argv):
    parser = argparse.ArgumentParser(description="table organizer")
    cmd_list = [v.name.upper() for v in DBOrganizerCmd]
    cmd_list.extend([v.name.lower() for v in DBOrganizerCmd])
    parser.add_argument("name", type=str, choices=cmd_list)

    args = parser.parse_args(argv[1:])
    return args


def start_func(db: Session, orgcmd: DBOrganizerCmd):
    cmnlog.deleteLogger(cmnlog.LogName.DB_ORGANIZE)
    cmnlog.createLogger(cmnlog.LogName.DB_ORGANIZE)
    if orgcmd == DBOrganizerCmd.ALL:
        pricelog_cleaner(db)
        sync_2days_to_pricelog_today(db)
        pricelog_2days_cleaner(db)
        return
    if orgcmd == DBOrganizerCmd.SYNC_PRICELOG:
        sync_2days_to_pricelog_today(db)
        return
    if orgcmd == DBOrganizerCmd.PRICELOG_2DAYS_CLEANER:
        pricelog_2days_cleaner(db)
        return
    if orgcmd == DBOrganizerCmd.PRICELOG_CLEANER:
        pricelog_cleaner(db)
        return
    return


def start_cmd(argv):
    param = param_parser(argv)
    if not param.name:
        print("No Param, Please cmd name")
        return
    cmnlog.createLogger(cmnlog.LogName.DB_ORGANIZE)
    db = next(get_session())
    for i in DBOrganizerCmd:
        if i.name.upper() == param.name.upper():
            print(f"start func {str(param.name).upper()}")
            start_func(db, orgcmd=i)
            print(f"end func {str(param.name).upper()}")
            break

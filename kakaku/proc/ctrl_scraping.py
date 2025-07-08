import argparse
from enum import auto
import time

from sqlalchemy.orm import Session

import psutil

from common.filter_name import AutoLowerName

from proc.scrapingmanage import sendTask
from proc.scrapingmanage.scrapingmanage import createScrapingManager

from proc.sendcmd import ScrOrder

from proc.get_sys_status import getSystemStatus
from proc.system_status import SystemStatus

from accessor.read_sqlalchemy import get_session


class ScrapingProcAction(AutoLowerName):
    START = auto()
    END = auto()
    RESTART = auto()


WAIT_PROC_EXIT_TIME = 0.5
TRY_WAIT_PROC_EXIT_TIME = 12

PROC_DEFAULT_ATTRS = ["pid", "name", "cmdline"]
START_PROCESS_NAME = "proc_manage.py"


def get_proc_info_all(attrs: list = PROC_DEFAULT_ATTRS) -> list:
    return [proc.info for proc in psutil.process_iter(attrs)]


def is_run_process(procname: str, self_ignore: bool = True) -> bool:
    if not procname:
        raise ValueError
    if len(procname) == 0:
        return False
    pl = get_proc_info_all()
    if self_ignore:
        self_pid = psutil.Process().as_dict(attrs=["pid"])
    for p in pl:
        for cmd in p["cmdline"]:
            if procname in cmd:
                if self_ignore and self_pid and p["pid"] == self_pid["pid"]:
                    continue
                return True
    return False


def parse_paramter(argv):
    parser = argparse.ArgumentParser(description="scraping process cntrol")
    parser.add_argument(
        "cmdorder",
        type=lambda x: x.lower(),
        choices=[v.value for v in ScrapingProcAction],
    )

    args = parser.parse_args(argv[1:])
    return args


def start_scrapingmanager():
    createScrapingManager()


def end_scrapingmanager():
    sendTask(cmdstr=ScrOrder.END)


def proc_action(db: Session, cmdname: str):
    if cmdname == ScrapingProcAction.START.value:
        if is_run_process(START_PROCESS_NAME, self_ignore=True):
            return
        sts_name = getSystemStatus(db)
        if sts_name == SystemStatus.STOP.name:
            start_scrapingmanager()
        return

    if not is_run_process(START_PROCESS_NAME, self_ignore=True):
        return

    if cmdname == ScrapingProcAction.END.value:
        end_scrapingmanager()
        return
    if cmdname == ScrapingProcAction.RESTART.value:
        sts_name = getSystemStatus(db)
        if (
            sts_name == SystemStatus.DURING_STARTUP.name
            or sts_name == SystemStatus.STOP.name
        ):
            return
        end_scrapingmanager()
        cnt: int = 0
        while cnt < TRY_WAIT_PROC_EXIT_TIME:
            time.sleep(WAIT_PROC_EXIT_TIME)
            cnt += 1
            sts_name = getSystemStatus(db)
            if sts_name == SystemStatus.STOP.name:
                start_scrapingmanager()
                break
            continue
        return
    return


def start_func(db: Session, act: ScrapingProcAction):
    proc_action(db, act.value)
    return


def start_cmd(argv):
    param = parse_paramter(argv)
    db = next(get_session())
    proc_action(db, param.cmdorder)
    return

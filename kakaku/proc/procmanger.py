import argparse
from enum import auto
import time

from common.filter_name import AutoLowerName

from proc.scrapingmanage import createScrapingManager, sendTask
from proc.sendcmd import ScrOrder

from proc.get_sys_status import getSystemStatus
from proc.system_status import SystemStatus


class ScrapingProcAction(AutoLowerName):
    START = auto()
    END = auto()
    RESTART = auto()


WAIT_PROC_EXIT_TIME = 0.5
TRY_WAIT_PROC_EXIT_TIME = 12


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
    sendTask(ScrOrder.END, "", -1)


def proc_action(cmdname: str):
    if cmdname == ScrapingProcAction.START.value:
        start_scrapingmanager()
        return
    if cmdname == ScrapingProcAction.END.value:
        end_scrapingmanager()
        return
    if cmdname == ScrapingProcAction.RESTART.value:
        end_scrapingmanager()
        cnt: int = 0
        while cnt < TRY_WAIT_PROC_EXIT_TIME:
            time.sleep(WAIT_PROC_EXIT_TIME)
            cnt += 1
            sts_name = getSystemStatus()
            if sts_name == SystemStatus.STOP.name:
                start_scrapingmanager()
                break
            continue
        return
    return


def start_func(act: ScrapingProcAction):
    proc_action(act.value)
    return


def start_cmd(argv):
    param = parse_paramter(argv)
    proc_action(param.cmdorder)
    return

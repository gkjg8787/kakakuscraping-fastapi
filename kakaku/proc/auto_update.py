import os
from datetime import datetime, timedelta, timezone
import re
from typing import Optional
from enum import Enum, unique
import time
from multiprocessing import Process
from logging import Logger


from common import util as cmn_util, read_config, cmnlog
from model.server import AutoUpdateSchedule
from proc import scrapingmanage as scm
from proc.sendcmd import ScrOrder
from proc.system_status import SystemStatusAccess, SystemStatus
from proc.system_status_log import SystemStatusLogAccess, SystemStatusLogName
from accessor.read_sqlalchemy import get_session, Session
from accessor.server import AutoUpdateScheduleQuery
from accessor.item.item import AutoUpdateItem
from accessor import store as ac_store


@unique
class AutoUpdateOnOff(Enum):
    ON = (1, "ON")
    OFF = (0, "OFF")

    def __init__(self, id: int, text: str):
        self.id = id
        self.ename = self.name.lower()
        self.jname = text


@unique
class AutoUpdateStatus(Enum):
    NONE = (0, "")
    NEXT = (1, "次回更新")
    WAIT = (2, "更新待機")
    UPDATED = (3, "更新済み")

    def __init__(self, id: int, text: str):
        self.id = id
        self.ename = self.name.lower()
        self.jname = text


def get_filename():
    return os.path.basename(__file__)


class DailyLogOrganizer:
    starttime: datetime
    logger: Logger

    def __init__(self, logger: Logger):
        self.setDatetime()
        self.logger = logger

    def run(self, reset=True):
        if cmn_util.isLocalToday(cmn_util.utcTolocaltime(self.starttime)):
            self.logger.debug(f"{get_filename()} localtoday = {self.starttime}")
            return
        self.logger.info(get_filename() + " sendTask " + ScrOrder.DB_ORGANIZE_DAYS)
        scm.sendTask(cmdstr=ScrOrder.DB_ORGANIZE_DAYS)
        if reset:
            self.logger.info(f"{get_filename()} {__class__.__name__} reset starttime")
            self.setDatetime()

    def setDatetime(self):
        self.starttime = datetime.now(timezone.utc)


class TwoDigitHourFormat:
    UPTIMEPTN: str = r"([0-9]{1,2}):([0-9]{2})"
    MAX_HOUR = 24
    MAX_MINUTE = 60

    @classmethod
    def checkFormat(cls, text: str, logger: Logger):
        ptn = re.compile(cls.UPTIMEPTN)
        ret = ptn.fullmatch(text)
        if not ret:
            logger.info(f"{get_filename()} no match updatetimeformat")
            return None
        hour = ret.group(1)
        if not hour.isdigit() or int(hour) < 0 or int(hour) >= cls.MAX_HOUR:
            logger.info(f"{get_filename()} hour is out of range")
            return None
        minute = ret.group(2)
        if not minute.isdigit() or int(minute) < 0 or int(minute) >= cls.MAX_MINUTE:
            logger.info(f"{get_filename()} minute is out of range")
            return None
        return ret.group(0)

    @classmethod
    def convert_to_two_digit_hour_str(cls, time_str: str):
        if len(time_str) == 5:
            return time_str
        tl = time_str.split(":")
        h = "{:02d}".format(int(tl[0]))
        m = "{:02d}".format(int(tl[1]))
        return f"{h}:{m}"

    @classmethod
    def convet_list_to_two_digit_hour_list(cls, time_str_list: str, logger: Logger):
        results: list[str] = []
        for upt in time_str_list:
            ret = cls.checkFormat(upt, logger)
            if not ret:
                logger.warning(f"{get_filename()} bad format = {upt}")
                continue
            logger.info(f"{get_filename()} set updatetime = {upt}")
            results.append(cls.convert_to_two_digit_hour_str(upt))
        return results

    @classmethod
    def convert_list_to_local_datetime_list(
        cls,
        time_str_list: list[str],
        logger: Logger | None = None,
        convert_tomorrow: bool = False,
    ):
        results: list[datetime] = []
        n = cmn_util.utcTolocaltime(datetime.now(timezone.utc))
        if convert_tomorrow:
            n = n + timedelta(days=1)
        ns = n.strftime("%Y%m%d ")
        tz = n.strftime("%z")
        input_fmt = "%Y%m%d %H:%M%z"
        for upts in time_str_list:
            results.append(datetime.strptime(ns + upts + tz, input_fmt))
        if logger:
            logger.debug(f"{get_filename()} updatelocaltime = {results}")
        return results

    @classmethod
    def convert_list_to_AutoUpdateSchedule_list(
        cls,
        timer_str_list: list[str],
        timer_list: list[datetime],
    ) -> list[AutoUpdateSchedule]:
        aus = AutoUpdateStatus
        if len(timer_str_list) == 1:
            return [
                AutoUpdateSchedule(requirement=timer_str_list[0], status=aus.NEXT.jname)
            ]
        reqs: list[AutoUpdateSchedule] = []
        near = None
        ln = cmn_util.utcTolocaltime(datetime.now(timezone.utc))
        for ult in timer_list:
            if ln < ult:
                if not near or near > ult:
                    near = ult
            continue

        s_fmt = "%H:%M"
        nearstr = None
        if near:
            nearstr = near.strftime(s_fmt)
        for ults in timer_str_list:
            if not nearstr:
                sts = aus.NONE.jname
            else:
                if nearstr == ults:
                    sts = aus.NEXT.jname
                elif nearstr < ults:
                    sts = aus.WAIT.jname
                else:
                    sts = aus.NONE.jname
            reqs.append(AutoUpdateSchedule(requirement=ults, status=sts))
        return reqs


class ItemAutoUpdateTimerFactory:
    @staticmethod
    def create(db: Session, logger: Logger):
        isAuto = read_config.is_auto_update_item()
        if not isAuto or not type(isAuto) is bool:
            isAuto = False
        upts = read_config.get_auto_update_time()
        if not upts or not type(upts) is list:
            logger.info(
                f"{get_filename()} {__class__.__name__} no updatetime list = {upts}"
            )
            isAuto = False
            upts = []
        iaut = ItemAutoUpdateTimer(
            isAutoUpdate=isAuto,
            db=db,
            logger=logger,
            updatelocaltimestrs=upts,
        )
        return iaut


class ItemAutoUpdateTimer:
    isAutoUpdate: bool
    updatelocaltimestrs: list[str]
    updatelocaltime: list[datetime]
    logger: Logger

    def __init__(
        self,
        isAutoUpdate: bool,
        db: Session,
        logger: Logger,
        updatelocaltimestrs: list[str] = [],
    ):
        self.logger = logger
        self.isAutoUpdate = isAutoUpdate
        if not isAutoUpdate:
            self.logger.info(f"{get_filename()} {__class__.__name__} set no autoupdate")
            return
        self.updatelocaltime = []
        self.updatelocaltimestrs = (
            TwoDigitHourFormat.convet_list_to_two_digit_hour_list(
                updatelocaltimestrs, logger
            )
        )
        self.createUpdateLocalTime()
        self.create_db_status(db=db)

    def create_db_status(self, db: Session):
        reqs = self.crate_AutoUpdateSchedule_list()
        dbret = AutoUpdateScheduleQuery.get_schedules(db)
        if len(dbret) == 0:
            AutoUpdateScheduleQuery.init_schedules(db=db, requirements=reqs)
            return
        if not self.equal_db_and_conf(dbret=dbret, conf=reqs):
            AutoUpdateScheduleQuery.init_schedules(db=db, requirements=reqs)
            return

        upreqs = [req for req in reqs if req.status != AutoUpdateStatus.NONE.jname]
        AutoUpdateScheduleQuery.update_status(db=db, requirements=upreqs)

    def equal_db_and_conf(
        self, dbret: list[AutoUpdateSchedule], conf: list[AutoUpdateSchedule]
    ):
        if len(dbret) != len(conf):
            return False
        dbretreqs: list[str] = [r.requirement for r in dbret]
        for c in conf:
            if c.requirement not in dbretreqs:
                return False
        return True

    def crate_AutoUpdateSchedule_list(self) -> list[AutoUpdateSchedule]:
        return TwoDigitHourFormat.convert_list_to_AutoUpdateSchedule_list(
            timer_str_list=self.updatelocaltimestrs, timer_list=self.updatelocaltime
        )

    def createUpdateLocalTime(self, tomorrow=False):
        self.updatelocaltime = TwoDigitHourFormat.convert_list_to_local_datetime_list(
            self.updatelocaltimestrs, logger=self.logger, convert_tomorrow=tomorrow
        )
        return

    def check_update_time(self, db: Session):
        lt = cmn_util.utcTolocaltime(datetime.now(timezone.utc))
        updated_time = None
        next_time = lt
        for uplt in sorted(self.updatelocaltime, reverse=True):
            if lt >= uplt:
                if not self.isUpdatefinished(db=db, start=uplt, end=next_time):
                    self.logger.info(
                        get_filename()
                        + " sendTask "
                        + ScrOrder.AUTO_UPDATE_ACT_ALL
                        + ", target="
                        + uplt.strftime("%H:%M")
                    )
                    scm.sendTask(cmdstr=ScrOrder.AUTO_UPDATE_ACT_ALL)
                    AutoUpdateScheduleQuery.update_status(
                        db=db,
                        requirements=[
                            AutoUpdateSchedule(
                                requirement=uplt.strftime("%H:%M"),
                                status=AutoUpdateStatus.UPDATED.jname,
                            )
                        ],
                    )
                updated_time = uplt
                break
            next_time = uplt
        self.removeUpdateTime(updated_time=updated_time)

    def run(self, db: Session, reset=True):
        if not self.isAutoUpdate:
            return
        self.logger.debug(f"{get_filename()} {__class__.__name__} run")
        self.check_update_time(db)
        if reset and len(self.updatelocaltime) == 0:
            self.logger.info(
                f"{get_filename()} {__class__.__name__} reset updatelocaltime"
            )
            self.createUpdateLocalTime(tomorrow=True)
            self.create_db_status(db=db)
        else:
            reqs = self.crate_AutoUpdateSchedule_list()
            upreqs = [req for req in reqs if req.status != AutoUpdateStatus.NONE.jname]
            AutoUpdateScheduleQuery.update_status(db=db, requirements=upreqs)

    def removeUpdateTime(self, updated_time: Optional[datetime]):
        if not updated_time or len(self.updatelocaltime) == 0:
            return
        self.logger.info(
            f"{get_filename()}"
            f"  {__class__.__name__} remove older than {updated_time} from updatelocaltime"
        )
        results = [upt for upt in self.updatelocaltime if upt > updated_time]
        self.updatelocaltime = results
        self.logger.debug(
            f"{get_filename()}"
            f"  {__class__.__name__} updatelocaltime = {self.updatelocaltime}"
        )

    def isUpdatefinished(self, db: Session, start: datetime, end: datetime):
        ret = SystemStatusLogAccess.get_count_by_systemstatus_and_datetime_range(
            db,
            syssts_name_list=[
                SystemStatusLogName.ALL_DATA_UPDATE,
                SystemStatusLogName.AUTO_ALL_DATA_UPDATE,
            ],
            start_time=start,
            end_time=end,
        )
        if ret:
            return True
        ret = AutoUpdateItem.get_pricelog_2days_count_by_date_range(
            db, start=start, end=end
        )
        self.logger.debug(
            f"get_pricelog_2days_count_by_date_range count={ret}, start={start}, end={end}"
        )
        if ret:
            return True
        return False


class DailyOnlineStoreUpdate:
    isAutoUpdate: bool
    updatelocaltimestrs: list[str]
    updatelocaltime: list[datetime]
    logger: Logger

    def __init__(self, logger: Logger):
        if not read_config.is_auto_update_online_store():
            logger.info(f"{get_filename()} {__class__.__name__} set no autoupdate")
            self.isAutoUpdate = False
            return
        upts = read_config.get_auto_update_online_store_time()
        if not upts or not type(upts) is list:
            logger.info(
                f"{get_filename()} {__class__.__name__} no updatetime list = {upts}"
            )
            self.isAutoUpdate = False
            return
        self.logger = logger
        self.updatelocaltime = []
        self.updatelocaltimestrs = (
            TwoDigitHourFormat.convet_list_to_two_digit_hour_list(upts, logger)
        )
        self.isAutoUpdate = True
        self.createUpdateLocalTime()

        return

    def createUpdateLocalTime(self, tomorrow=False):
        self.updatelocaltime = TwoDigitHourFormat.convert_list_to_local_datetime_list(
            self.updatelocaltimestrs, logger=self.logger, convert_tomorrow=tomorrow
        )
        return

    def check_update_time(self, db: Session):
        lt = cmn_util.utcTolocaltime(datetime.now(timezone.utc))
        updated_time = None
        next_time = lt
        for uplt in sorted(self.updatelocaltime, reverse=True):
            if lt >= uplt:
                if not self.isUpdatefinished(db=db, start=uplt, end=next_time):
                    self.logger.info(
                        get_filename()
                        + " sendTask "
                        + ScrOrder.UPDATE_ONLINE_STORE_POSTAGE
                    )
                    scm.sendTask(cmdstr=ScrOrder.UPDATE_ONLINE_STORE_POSTAGE)
                updated_time = uplt
                break
            next_time = uplt
        self.removeUpdateTime(updated_time=updated_time)

    def run(self, db: Session, reset=True):
        if not self.isAutoUpdate:
            return
        self.logger.debug(f"{get_filename()} {__class__.__name__} run")
        self.check_update_time(db)
        if reset and len(self.updatelocaltime) == 0:
            self.logger.info(
                f"{get_filename()} {__class__.__name__} reset updatelocaltime"
            )
            self.createUpdateLocalTime(tomorrow=True)

    def removeUpdateTime(self, updated_time: Optional[datetime]):
        if not updated_time or len(self.updatelocaltime) == 0:
            return
        self.logger.info(
            f"{get_filename()}"
            f" {__class__.__name__} remove older than {updated_time} from updatelocaltime"
        )
        results = [upt for upt in self.updatelocaltime if upt > updated_time]
        self.updatelocaltime = results
        self.logger.debug(
            f"{get_filename()}"
            f" {__class__.__name__} updatelocaltime = {self.updatelocaltime}"
        )

    def isUpdatefinished(self, db: Session, start: datetime, end: datetime):
        update_count = (
            SystemStatusLogAccess.get_count_by_systemstatus_and_datetime_range(
                db,
                syssts_name_list=[SystemStatusLogName.ONLINE_STORE_UPDATE],
                start_time=start,
                end_time=end,
            )
        )
        if update_count > 1:
            return True
        not_update_store_count = (
            ac_store.OnlineStoreQuery.get_count_postage_not_updated_today(db)
        )
        if not not_update_store_count:
            return True
        return False


class TimerProc:
    dlo: DailyLogOrganizer
    iaut: ItemAutoUpdateTimer
    dosu: DailyOnlineStoreUpdate
    proc_list: list[Process]
    DEFAULT_CYCLT_TIME: float = 3.0
    MIN_CYCLE_TIME: float = 1

    def __init__(self):
        logger = cmnlog.createLogger(cmnlog.LogName.TIMER)
        logger.info(f"{get_filename()} init timer process")
        self.proc_list = []

    def start(self):
        logger = cmnlog.getLogger(cmnlog.LogName.TIMER)
        logger.info(f"{get_filename()} start timer process")

        with next(get_session()) as db:
            self.iaut = ItemAutoUpdateTimerFactory.create(db=db, logger=logger)
        if self.iaut.isAutoUpdate:
            iutproc = Process(
                target=self.run_itemupdatetimer,
                args=(read_config.get_auto_update_check_cycle_time(),),
            )
            self.proc_list.append(iutproc)
            logger.info(f"{get_filename()} start ItemAutoUpdateTimer")

        self.dlo = DailyLogOrganizer(logger)
        dloproc = Process(
            target=self.run_dailylogorganizer,
            args=(read_config.get_auto_db_organizer_check_cycle_time(),),
        )
        self.proc_list.append(dloproc)
        logger.info(f"{get_filename()} start DailyOrganizer")

        self.dosu = DailyOnlineStoreUpdate(logger)
        if self.dosu.isAutoUpdate:
            osuproc = Process(
                target=self.run_onlinestoreupdate,
                args=(read_config.get_auto_update_online_store_cycle_time(),),
            )
            self.proc_list.append(osuproc)
            logger.info(f"{get_filename()} start DailyOnlineStoreUpdate")

        for p in self.proc_list:
            p.start()

    def end(self):
        for p in self.proc_list:
            p.terminate()
        time.sleep(0.1)
        self.proc_list.clear()
        logger = cmnlog.getLogger(cmnlog.LogName.TIMER)
        logger.info(f"{get_filename()} end timer process")

    @classmethod
    def actSystemStatus(cls, db: Session) -> bool:
        syssts = SystemStatusAccess()
        syssts.update(db=db)
        if SystemStatus.ACTIVE == syssts.getStatus():
            return True
        return False

    def run_itemupdatetimer(self, cycle_time: float):
        if cycle_time < self.MIN_CYCLE_TIME:
            cycle_time = self.MIN_CYCLE_TIME
        while True:
            with next(get_session()) as db:
                if not self.actSystemStatus(db):
                    time.sleep(cycle_time)
                    continue
                self.iaut.run(db)
            time.sleep(cycle_time)

    def run_dailylogorganizer(self, cycle_time: float):
        if cycle_time < self.MIN_CYCLE_TIME:
            cycle_time = self.MIN_CYCLE_TIME
        while True:
            with next(get_session()) as db:
                if not self.actSystemStatus(db):
                    time.sleep(cycle_time)
                    continue
            self.dlo.run()
            time.sleep(cycle_time)

    def run_onlinestoreupdate(self, cycle_time: float):
        if cycle_time < self.MIN_CYCLE_TIME:
            cycle_time = self.MIN_CYCLE_TIME
        while True:
            with next(get_session()) as db:
                if not self.actSystemStatus(db):
                    time.sleep(cycle_time)
                    continue
                self.dosu.run(db)
            time.sleep(cycle_time)

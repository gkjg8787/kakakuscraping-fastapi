import os
from datetime import datetime, timedelta
import re
from typing import Optional
from logging import Logger
from enum import Enum, unique

from sqlalchemy.orm import Session

from common import util as cmn_util
from common import read_config

from proc import scrapingmanage as scm
from proc.sendcmd import ScrOrder

from accessor.item.item import AutoUpdateItem

from proc.system_status import SystemStatusAccess, SystemStatus

from model.server import AutoUpdateSchedule
from accessor.server import AutoUpdateScheduleQuery

@unique
class AutoUpdateOnOff(Enum):
    ON = (1, "ON")
    OFF = (0, "OFF")
    def __init__(self, id :int, text :str):
        self.id = id
        self.ename = self.name.lower()
        self.jname = text
@unique
class AutoUpdateStatus(Enum):
    NONE = (0, "")
    NEXT = (1, "次回更新")
    WAIT = (2, "更新待機")
    UPDATED = (3, "更新済み")

    def __init__(self, id :int, text :str):
        self.id = id
        self.ename = self.name.lower()
        self.jname = text

def get_filename():
    return os.path.basename(__file__)

class DailyLogOrganizer:
    starttime : datetime
    logger :Logger

    def __init__(self, logger :Logger):
        self.setDatetime()
        self.logger = logger

    def run(self, reset=True):
        if cmn_util.isLocalToday(cmn_util.utcTolocaltime(self.starttime)):
            self.logger.debug(f"{get_filename()} localtoday = {self.starttime}")
            return
        self.logger.info(get_filename() + " sendTask "+ ScrOrder.DB_ORGANIZE_DAYS)
        scm.sendTask(ScrOrder.DB_ORGANIZE_DAYS, "", "")
        if reset:
            self.logger.info(get_filename() + " DailyLogOrganizer reset starttime")
            self.setDatetime()
        
    def setDatetime(self):
        self.starttime = datetime.utcnow()

class ItemAutoUpdateTimer:
    UPTIMEPTN :str = r"([0-9]{1,2}):([0-9]{2})"
    MAX_HOUR = 24
    MAX_MINUTE = 60

    isAutoUpdate : bool
    updatelocaltimestrs :list[str]
    updatelocaltime :list[datetime]
    logger :Logger

    def __init__(self, isAutoUpdate :bool,
                 db :Session,
                 logger :Logger,
                 updatelocaltimestrs :list[str] = [],
                 ):
        self.logger = logger
        self.isAutoUpdate = isAutoUpdate
        if not isAutoUpdate:
            self.logger.info(get_filename() + "set no autoupdate")
            return
        self.updatelocaltime = []
        self.updatelocaltimestrs = []
        for upt in updatelocaltimestrs:
            ret = self.checkUpdateTimeFormat(upt)
            if not ret:
                self.logger.warning(f"{get_filename()} bad format = {upt}")
                continue
            self.logger.info(f"{get_filename()} set updatetime = {upt}")
            self.updatelocaltimestrs.append(self.convert_to_two_digit_hour_str(upt))
        
        self.createUpdateLocalTime()
        self.create_db_status(db=db)
    
    def convert_to_two_digit_hour_str(self, time_str :str):
        if len(time_str) == 5:
            return time_str
        tl = time_str.split(":")
        h = "{:02d}".format(int(tl[0]))
        m = "{:02d}".format(int(tl[1]))
        return f"{h}:{m}"
    
    def create_db_status(self, db :Session):
        reqs = self.crate_AutoUpdateSchedule_list()
        dbret = AutoUpdateScheduleQuery.get_schedules(db)
        if len(dbret) == 0:
            AutoUpdateScheduleQuery.init_schedules(db=db, requirements=reqs)
            return
        if not self.equal_db_and_conf(dbret=dbret, conf=reqs):
            AutoUpdateScheduleQuery.init_schedules(db=db, requirements=reqs)
            return

        upreqs = [ req for req in reqs if req.status != AutoUpdateStatus.NONE.jname ]
        AutoUpdateScheduleQuery.update_status(db=db, requirements=upreqs)

    
    def equal_db_and_conf(self, dbret :list[AutoUpdateSchedule], conf :list[AutoUpdateSchedule]):
        if len(dbret) != len(conf):
            return False
        dbretreqs :list[str]= [ r.requirement for r in dbret ]
        for c in conf:
            if not c.requirement in dbretreqs:
                return False
        return True
    
    def crate_AutoUpdateSchedule_list(self) -> list[AutoUpdateSchedule]:
        aus = AutoUpdateStatus
        if len(self.updatelocaltimestrs) == 1:
            return [AutoUpdateSchedule(requirement=self.updatelocaltimestrs[0],
                                       status=aus.NEXT.jname)]
        reqs :list[AutoUpdateSchedule]= []
        near = None
        ln = cmn_util.utcTolocaltime(datetime.utcnow())
        for ult in self.updatelocaltime:
            if ln < ult:
                if not near or near > ult:
                    near = ult
            continue

        s_fmt = "%H:%M"
        nearstr = None
        if near:
            nearstr = near.strftime(s_fmt)
        for ults in self.updatelocaltimestrs:
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
        
    
    @staticmethod
    def create(db :Session, logger :Logger):
        isAuto = read_config.is_auto_update_item()
        if not isAuto\
            or not type(isAuto) is bool:
            isAuto = False
        upts = read_config.get_auto_update_time()
        if not upts\
            or not type(upts) is list:
            logger.info(f"{get_filename()} no updatetime list = {upts}")
            isAuto = False
            upts = []
        iaut = ItemAutoUpdateTimer(isAutoUpdate=isAuto,
                                   db=db,
                                   logger=logger,
                                   updatelocaltimestrs=upts,
                                   )
        return iaut
    
    def createUpdateLocalTime(self, tomorrow=False):
        self.updatelocaltime = []
        n = cmn_util.utcTolocaltime(datetime.utcnow())
        if tomorrow:
            n = n + timedelta(days=1)
        ns = n.strftime("%Y%m%d ")
        tz = n.strftime("%z")
        input_fmt = "%Y%m%d %H:%M%z"
        for upts in self.updatelocaltimestrs:
            self.updatelocaltime.append(datetime.strptime(ns + upts + tz, input_fmt))
        self.logger.debug(f'{get_filename()} updatelocaltime = {self.updatelocaltime}')

    def checkUpdateTimeFormat(self, text :str):
        ptn = re.compile(self.UPTIMEPTN)
        ret = ptn.fullmatch(text)
        if not ret:
            self.logger.info(f'{get_filename()} no match updatetimeformat')
            return None
        hour = ret.group(1)
        if not hour.isdigit() or int(hour) < 0 or int(hour) >= self.MAX_HOUR:
            self.logger.info(f'{get_filename()} hour is out of range')
            return None
        minute = ret.group(2)
        if not minute.isdigit() or int(minute) < 0 or int(minute) >= self.MAX_MINUTE:
            self.logger.info(f'{get_filename()} minute is out of range')
            return None
        return ret.group(0)
    
    def run(self, db :Session, reset=True):
        if not self.isAutoUpdate:
            return
        lt = cmn_util.utcTolocaltime(datetime.utcnow())
        updated_time = None
        next_time = lt
        self.logger.debug(f"{get_filename()} ItemAutoUpdateTimer run")
        for uplt in sorted(self.updatelocaltime, reverse=True):
            if lt >= uplt:
                if not self.isUpdatefinished(db=db, start=uplt, end=next_time):
                    self.logger.info(get_filename() + " sendTask "+ ScrOrder.UPDATE_ACT_ALL + ", target=" + uplt.strftime("%H:%M"))
                    scm.sendTask(ScrOrder.UPDATE_ACT_ALL, '', '')
                    AutoUpdateScheduleQuery.update_status(db=db,
                                                          requirements=[AutoUpdateSchedule(requirement=uplt.strftime("%H:%M"),
                                                                                           status=AutoUpdateStatus.UPDATED.jname
                                                                                           )]
                                                        )
                updated_time = uplt
                break
            next_time = uplt
        self.removeUpdateTime(updated_time=updated_time)
        if reset\
            and len(self.updatelocaltime) == 0:
            self.logger.info(f"{get_filename()} ItemAutoUpdateTimer reset updatelocaltime")
            self.createUpdateLocalTime(tomorrow=True)
            self.create_db_status(db=db)
        else:
            reqs = self.crate_AutoUpdateSchedule_list()
            upreqs = [ req for req in reqs if req.status != AutoUpdateStatus.NONE.jname ]
            AutoUpdateScheduleQuery.update_status(db=db, requirements=upreqs)

    
    def removeUpdateTime(self, updated_time :Optional[datetime]):
        if not updated_time\
            or len(self.updatelocaltime) == 0:
            return
        self.logger.info(f'{get_filename()} remove older than {updated_time} from updatelocaltime')
        results = [upt for upt in self.updatelocaltime if upt > updated_time]
        self.updatelocaltime = results
        self.logger.debug(f'{get_filename()} updatelocaltime = {self.updatelocaltime}')
    
    def isUpdatefinished(self, db :Session, start :datetime, end :datetime):
        ret = AutoUpdateItem.get_pricelog_2days_count_by_date_range(db, start=start, end=end)
        self.logger.debug(f'get_pricelog_2days_count_by_date_range count={ret}, start={start}, end={end}')
        if ret:
            return True
        return False
    
class UpdateTimer:
    dlo :DailyLogOrganizer
    iaut :ItemAutoUpdateTimer

    def __init__(self, db :Session, logger :Logger):
        self.dlo = DailyLogOrganizer(logger)
        self.iaut = ItemAutoUpdateTimer.create(db=db, logger=logger)
    
    def actSystemStatus(self, db :Session) -> bool:
        syssts = SystemStatusAccess()
        syssts.update(db=db)
        if SystemStatus.ACTIVE == syssts.getStatus():
            return True
        return False

    def run(self, db :Session):
        if not self.actSystemStatus(db):
            return
        self.dlo.run()
        self.iaut.run(db=db)
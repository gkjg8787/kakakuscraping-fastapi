from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess
from multiprocessing import Process, Manager, Queue
import queue

from sqlalchemy.orm import Session

from . import BaseTemplateValue
from parameter_parser.admin import ProcCtrlForm, LogFilterQuery
from proc.system_status import SystemStatus, SystemStatusToJName
from proc import get_sys_status
from proc.auto_update import AutoUpdateOnOff, TwoDigitHourFormat
from proc.system_status_log import SystemStatusLogAccess
from proc.server_log import (
    IExtractServerLog,
    ExtractServerLogResult,
    ExtractServerLogByCommand,
)
from proc.temp_file import CountTempFile, CountTempFileResult
from common import read_config, templates_string
from common.filter_name import (
    FilterQueryName,
    SystemCtrlBtnName,
    DashBoardPostName,
    OnlineStoreCopyTypeName,
    LogLevelFilterName,
)
from common.util import utcTolocaltime, JST
from common.cmnlog import getLogger, LogName
from model.server import AutoUpdateSchedule
from accessor.server import AutoUpdateScheduleQuery

from . import shared
from .shared import factory as shared_factory

SYSTEM_STS_LOG_DEFAULT = "表示するログがありません"


class DashBoardTemplate(BaseTemplateValue):
    system_ctrl_btn_name: str = DashBoardPostName.SYSTEM_CTRL_BTN.value
    STARTUP: str = SystemCtrlBtnName.STARTUP.value
    STOP: str = SystemCtrlBtnName.STOP.value
    RESTART: str = SystemCtrlBtnName.RESTART.value
    syssts: str = SystemStatus.NONE.name
    sysstop: bool = True
    item_autoupdate: str = AutoUpdateOnOff.OFF.jname
    item_autoupdate_schedule: list[AutoUpdateSchedule] = []
    online_store_autoupdate: str = AutoUpdateOnOff.OFF.jname
    online_store_autoupdate_schedule: list[AutoUpdateSchedule] = []
    sysstatuslog: str = SYSTEM_STS_LOG_DEFAULT
    auto_copy_online_store_to_local: str = AutoUpdateOnOff.OFF.jname
    auto_copy_online_store_to_local_internal_config: dict

    def __init__(self, db: Session):
        super().__init__(auto_copy_online_store_to_local_internal_config={})
        syssts = get_sys_status.getSystemStatus(db)
        self.syssts = SystemStatusToJName.get_jname(syssts)
        if syssts == SystemStatus.STOP.name:
            self.sysstop = True
        else:
            self.sysstop = False

        if read_config.is_auto_update_item():
            self.item_autoupdate = AutoUpdateOnOff.ON.jname
            self.item_autoupdate_schedule = AutoUpdateScheduleQuery.get_schedules(db)

        if read_config.is_auto_update_online_store():
            self.online_store_autoupdate = AutoUpdateOnOff.ON.jname
            self.online_store_autoupdate_schedule = (
                self.create_online_store_autoupdate_schedule()
            )

        if self.is_auto_copy_online_store_to_local():
            self.auto_copy_online_store_to_local = AutoUpdateOnOff.ON.jname
            self.auto_copy_online_store_to_local_internal_config = (
                self.get_auto_copy_online_store_to_local_internal_config()
            )

        self.sysstatuslog = self.get_system_status_log_text(db)

    @classmethod
    def get_system_status_log_text(cls, db: Session) -> str:
        sysstslogs = SystemStatusLogAccess.get_all(db=db)
        printlogs: list[str] = []
        for log in sysstslogs:
            printlogs.append(f"{utcTolocaltime(log.created_at)} : {log.status}")
        if len(printlogs) > 0:
            return "\n".join(printlogs)
        return SYSTEM_STS_LOG_DEFAULT

    @classmethod
    def create_online_store_autoupdate_schedule(cls):
        results: list[AutoUpdateSchedule] = []
        up_str_list: list[str] = TwoDigitHourFormat.convet_list_to_two_digit_hour_list(
            read_config.get_auto_update_online_store_time(), getLogger(LogName.CLIENT)
        )
        up_list: list[datetime] = (
            TwoDigitHourFormat.convert_list_to_local_datetime_list(
                time_str_list=up_str_list,
                convert_tomorrow=cls.is_update_for_today_complete(up_str_list),
            )
        )
        results = TwoDigitHourFormat.convert_list_to_AutoUpdateSchedule_list(
            timer_str_list=up_str_list, timer_list=up_list
        )
        return results

    @classmethod
    def is_update_for_today_complete(cls, timer_str_list: list[str]):
        now = utcTolocaltime(datetime.now(timezone.utc)).strftime("%H:%M")
        if len(timer_str_list) == 0:
            return False
        if now > sorted(timer_str_list, reverse=True)[0]:
            return True
        return False

    @classmethod
    def is_auto_copy_online_store_to_local(cls):
        auto_set = read_config.get_auto_copy_of_online_store_info_to_local()
        if not auto_set:
            return False
        if "auto" not in auto_set or auto_set["auto"] is None:
            return False
        if type(auto_set["auto"]) is not bool:
            return False
        return auto_set["auto"]

    @classmethod
    def get_auto_copy_online_store_to_local_internal_config(cls):
        auto_set = read_config.get_auto_copy_of_online_store_info_to_local()
        results = {}
        if not auto_set:
            return results
        if "type" not in auto_set or auto_set["type"] is None:
            return results
        for osctn in OnlineStoreCopyTypeName:
            if str(auto_set["type"]).lower().replace(
                "_", ""
            ) == osctn.qname.lower().replace("_", ""):
                results["name"] = "コピータイプ"
                results["value"] = osctn.jname
                return results
        return results


class BackServerCtrl:
    CMD_NAME = "proc_manage.py"
    cmd_msg: str = ""

    def __init__(self, pcf: ProcCtrlForm):
        self.cmd_msg = pcf.proc_action

    def action(self):
        base_path = str(read_config.get_srcdir())
        cmd = ["python3", str(Path(base_path, self.CMD_NAME))]
        if self.cmd_msg == SystemCtrlBtnName.STARTUP.value:
            cmd.append("start")
        if self.cmd_msg == SystemCtrlBtnName.STOP.value:
            cmd.append("end")
        if self.cmd_msg == SystemCtrlBtnName.RESTART.value:
            cmd.append("restart")
        subprocess.run(cmd)


class LogLevelFilterFactory:
    @classmethod
    def create(
        cls,
        input_name: str = FilterQueryName.LEVEL.value,
        selected_id_list: list[int] = [],
    ) -> shared.CheckBox:
        checkboxelist: list[shared.CheckBoxElement] = []
        for s in LogLevelFilterName:
            checkbox = shared.CheckBoxElement(id=s.id, text=s.jname, checked="")
            if selected_id_list and s.id in selected_id_list:
                checkbox.checked = templates_string.HTMLOption.CHECKED.value
            checkboxelist.append(checkbox)
        return shared.CheckBox(
            input_name=input_name,
            checkboxes=checkboxelist,
        )


class ServerLogDisplay(BaseTemplateValue):
    logfilelist: list[ExtractServerLogResult]
    fquery: dict
    date_range_filter: shared.RangeInputForm
    loglevel_filter: shared.CheckBox

    def __init__(self, lfq: LogFilterQuery):
        today = datetime.now(timezone.utc)
        one_year_ago = today - timedelta(days=365)
        datefmt = "%Y-%m-%d"
        selected_id_list: list[int] = []
        if lfq.level_list:
            selected_id_list = [int(level) for level in lfq.level_list]
        if not lfq.level_list and not lfq.min_date and not lfq.max_date:
            lfq.min_date = (today - timedelta(days=3)).astimezone(JST).strftime(datefmt)
        super().__init__(
            logfilelist=[],
            fquery={},
            date_range_filter=shared_factory.DateRangeFilterFactory.create(
                lower_value=lfq.min_date,
                upper_value=lfq.max_date,
                lower_max=today,
                upper_max=today,
                lower_min=one_year_ago,
                upper_min=one_year_ago,
            ),
            loglevel_filter=LogLevelFilterFactory.create(
                selected_id_list=selected_id_list
            ),
        )
        self.logfilelist = self.get_logfilelist(
            lfq=lfq, datefmt=datefmt, selected_id_list=selected_id_list
        )

    def get_logfilelist(
        self, lfq: LogFilterQuery, datefmt: str, selected_id_list: list[int]
    ) -> list[ExtractServerLogResult]:
        start_date: datetime | None = None
        end_date: datetime | None = None
        if lfq.max_date:
            end_date = datetime.strptime(lfq.max_date, datefmt)
        if lfq.min_date:
            start_date = datetime.strptime(lfq.min_date, datefmt)
        loglevel_name_list: list[str] = []
        if selected_id_list:
            for lname in LogLevelFilterName:
                if lname.id in selected_id_list:
                    loglevel_name_list.append(lname.name)

        loglist = self.get_logname_list()
        esl = ExtractServerLogByCommand()
        proclist: list[Process] = []
        m = Manager()
        retq: Queue = m.Queue()
        timeout: float = 10.0
        for logfile in loglist:
            p = Process(
                target=self.start_func_for_process,
                args=(
                    logfile,
                    loglevel_name_list,
                    start_date,
                    end_date,
                    esl,
                    retq,
                    timeout,
                ),
            )
            p.start()
            proclist.append(p)

        for p in proclist:
            p.join()

        logfilelist: list[ExtractServerLogResult] = []
        for p in proclist:
            try:
                eslresult: ExtractServerLogResult = retq.get(timeout=timeout)
                logfilelist.append(eslresult)
            except queue.Empty:
                pass
        return sorted(logfilelist, key=lambda logf: logf.filename)

    @staticmethod
    def start_func_for_process(
        logname: str,
        loglevel_name_list: list[str],
        start: datetime | None,
        end: datetime | None,
        esl: IExtractServerLog,
        retq: Queue,
        timeout: float = 10,
    ):
        eslresult = esl.get_list_by_time_period(
            logname=logname,
            loglevel_name_list=loglevel_name_list,
            start=start,
            end=end,
        )
        if eslresult.error_msg:
            eslresult.text = eslresult.error_msg
        retq.put(eslresult, timeout=timeout)

    @staticmethod
    def get_logname_list():
        return [
            LogName.CLIENT,
            LogName.MANAGER,
            LogName.DOWNLOAD,
            LogName.DOWNLOAD + "{:0=2}".format(0),
            LogName.DOWNLOAD + "{:0=2}".format(1),
            LogName.DOWNLOAD + "{:0=2}".format(2),
            LogName.PARSE,
            LogName.ITEMCOMB,
            LogName.SEARCH,
            LogName.DB_ORGANIZE,
            LogName.TIMER,
        ]


class TempDirDisplay(BaseTemplateValue):
    counttempfile: CountTempFileResult

    def __init__(self):
        super().__init__(counttempfile=CountTempFile().execute())

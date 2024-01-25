from datetime import datetime
from pathlib import Path
import subprocess

from sqlalchemy.orm import Session

from template_value import BaseTemplateValue

from proc.system_status import SystemStatus, SystemStatusToJName
from parameter_parser.admin import ProcCtrlForm
from proc import get_sys_status
from common import read_config
from common.filter_name import (
    SystemCtrlBtnName,
    DashBoardPostName,
)
from common.util import utcTolocaltime
from proc.auto_update import AutoUpdateOnOff, TwoDigitHourFormat
from model.server import AutoUpdateSchedule
from accessor.server import AutoUpdateScheduleQuery
from proc.system_status_log import SystemStatusLogAccess
from common.cmnlog import getLogger, LogName


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

    def __init__(self, request, db: Session):
        super().__init__(request=request)
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
        up_list: list[
            datetime
        ] = TwoDigitHourFormat.convert_list_to_local_datetime_list(
            time_str_list=up_str_list,
            convert_tomorrow=cls.is_update_for_today_complete(up_str_list),
        )
        results = TwoDigitHourFormat.convert_list_to_AutoUpdateSchedule_list(
            timer_str_list=up_str_list, timer_list=up_list
        )
        return results

    @classmethod
    def is_update_for_today_complete(cls, timer_str_list: list[str]):
        now = utcTolocaltime(datetime.utcnow()).strftime("%H:%M")
        if len(timer_str_list) == 0:
            return False
        if now > sorted(timer_str_list, reverse=True)[0]:
            return True
        return False


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

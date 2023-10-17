
from pathlib import Path
import subprocess

from sqlalchemy.orm import Session

from template_value.item import BaseTemplateValue

from proc.system_status import SystemStatus, SystemStatusToJName
from parameter_parser.admin import ProcCtrlForm
from proc import get_sys_status
from common.filter_name import (
    SystemCtrlBtnName,
    DashBoardPostName,
)
class DashBoardTemplate(BaseTemplateValue):
    system_ctrl_btn_name :str = DashBoardPostName.SYSTEM_CTRL_BTN.value
    STARTUP:str = SystemCtrlBtnName.STARTUP.value
    STOP :str = SystemCtrlBtnName.STOP.value
    RESTART :str = SystemCtrlBtnName.RESTART.value
    syssts :str = SystemStatus.NONE.name
    sysstop :bool = True

    def __init__(self, request, db :Session):
        super().__init__(request=request)
        syssts = get_sys_status.getSystemStatus(db)
        self.syssts = SystemStatusToJName.get_jname(syssts)
        if syssts == SystemStatus.STOP.name:
            self.sysstop = True
        else:
            self.sysstop = False

class BackServerCtrl:
    CMD_NAME = "proc_manage.py"
    cmd_msg :str = ""

    def __init__(self, pcf :ProcCtrlForm):
        self.cmd_msg = pcf.proc_action

    def action(self):
        base_path = Path(__file__).resolve().parent.parent
        cmd = ["python3", str(Path(base_path, self.CMD_NAME))]
        if self.cmd_msg == SystemCtrlBtnName.STARTUP.value:
            cmd.append("start")
        if self.cmd_msg == SystemCtrlBtnName.STOP.value:
            cmd.append("end")
        if self.cmd_msg == SystemCtrlBtnName.RESTART.value:
            cmd.append("restart")
        subprocess.run(cmd)

    




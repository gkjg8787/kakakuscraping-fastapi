
from template_value.item import BaseTemplateValue

from proc.system_status import SystemStatus, SystemStatusToJName
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

    def __init__(self, request):
        super().__init__(request=request)
        syssts = get_sys_status.getSystemStatus()
        self.syssts = SystemStatusToJName.get_jname(syssts)
        if syssts == SystemStatus.STOP.name:
            self.sysstop = True
        else:
            self.sysstop = False


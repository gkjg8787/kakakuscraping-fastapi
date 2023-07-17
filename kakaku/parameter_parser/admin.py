
from fastapi import Form

from common.filter_name import (
    SystemCtrlBtnName,
)

class ProcCtrlForm:
    proc_action: str = None

    def __init__(self, system_ctrl_btn :str = Form()):
        if system_ctrl_btn in [v.value for v in SystemCtrlBtnName]:
            self.proc_action = system_ctrl_btn
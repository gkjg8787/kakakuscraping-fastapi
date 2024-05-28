from datetime import datetime

from fastapi import Form, Query

from common.filter_name import (
    FilterQueryName,
    SystemCtrlBtnName,
    LogLevelFilterName,
)


class ProcCtrlForm:
    proc_action: str = None

    def __init__(self, system_ctrl_btn: str = Form()):
        if system_ctrl_btn in [v.value for v in SystemCtrlBtnName]:
            self.proc_action = system_ctrl_btn


class LogFilterQuery:
    level_list: list[str]
    min_date: str = ""
    max_date: str = ""

    def __init__(
        self, level: list[str] = Query([]), min_date: str = "", max_date: str = ""
    ):
        self.level_list = []
        for l in level:
            if self.is_valid_log_level(l):
                self.level_list.append(l)
        if min_date and self.is_valid_date(min_date):
            self.min_date = min_date
        if max_date and self.is_valid_date(max_date):
            self.max_date = max_date

    def is_valid_log_level(self, value: str):
        if not value or not value.isdigit():
            return False
        for lfq in LogLevelFilterName:
            if int(value) == lfq.id:
                return True
        return False

    def is_valid_date(self, value: str):
        fmt = "%Y-%m-%d"
        try:
            d = datetime.strptime(value, fmt)
        except Exception as e:
            return False
        return True

    def get_filter_dict(self) -> dict:
        results = {}
        if self.level_list:
            results[FilterQueryName.LEVEL.value] = self.level_list
        if self.min_date:
            results[FilterQueryName.MIN_DATE.value] = self.min_date
        if self.max_date:
            results[FilterQueryName.MAX_DATE.value] = self.max_date
        return results

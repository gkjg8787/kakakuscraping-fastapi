import os
import subprocess
from datetime import datetime
from abc import ABCMeta, abstractmethod

from pydantic import BaseModel

from common import cmnlog, filter_name
from .service import ServerLogRawText
from .model import ServerLogFile, ServerLogLine
from .file import ServerLogFileFactory


class ExtractServerLogResult(BaseModel):
    filename: str
    text: str = ""
    error_msg: str = ""


class IExtractServerLog(metaclass=ABCMeta):
    @abstractmethod
    def get_list_by_time_period(
        self,
        logname: str,
        start: datetime | None = None,
        end: datetime | None = None,
        loglevel_name_list: list[str] = [],
    ) -> ExtractServerLogResult:
        pass


class CreateExtractServerLogCommand:
    def get_command(
        self,
        fpath: str,
        start: datetime | None,
        end: datetime | None,
        loglevel_name_list: list[str],
    ) -> str:
        datefmt = "%Y-%m-%d"
        cmd = ""
        if start and end and start == end:
            cmd = f"grep '{start.strftime(datefmt)}' {fpath}"
        elif start or end:
            datelist_of_file = self.get_datelist_of_file(fpath=fpath)
            if start and end:
                date_count_in_range = self.get_count_of_date_in_range(
                    datelist=datelist_of_file, start=start, end=end
                )
                if not date_count_in_range:
                    return f"grep '{start.strftime(datefmt)}' {fpath}"
            near_start = self.get_closest_start_date(
                datelist=datelist_of_file, start=start, end=end
            )
            near_end = self.get_closest_day_following_end_date(
                datelist=datelist_of_file, end=end, start=start
            )
            if near_start and near_end:
                if near_start.date() != near_end.date():
                    cmd = "sed -n '/%s/,$p' %s | awk '/%s/ {exit} {print}'" % (
                        near_start.strftime(datefmt),
                        fpath,
                        near_end.strftime(datefmt),
                    )
                else:
                    cmd = f"grep '{near_start.strftime(datefmt)}' {fpath}"
            elif near_start:
                cmd = "sed -n '/%s/,$p' %s" % (near_start.strftime(datefmt), fpath)
            elif near_end:
                cmd = "awk '/%s/ {exit} {print}' %s" % (
                    near_end.strftime(datefmt),
                    fpath,
                )
        if loglevel_name_list and not self.is_all_loglevel(
            loglevel_name_list=loglevel_name_list
        ):
            ret: str = ""
            for l in loglevel_name_list:
                if ret:
                    ret += f"|{l}"
                else:
                    ret = f"{l}"
            if ret:
                if cmd:
                    cmd += f" | grep -E '({ret})'"
                else:
                    cmd = f"grep -E '({ret})' {fpath}"
        return cmd

    @staticmethod
    def is_all_loglevel(loglevel_name_list: list[str]) -> bool:
        if not loglevel_name_list:
            return False
        ret: set[str] = set()
        loglevelfilter_len: int = 0
        for lfq in filter_name.LogLevelFilterName:
            loglevelfilter_len += 1
            if lfq.jname in loglevel_name_list:
                ret.add(lfq.jname)
        if len(ret) == loglevelfilter_len:
            return True
        return False

    def get_datelist_of_file(self, fpath: str):
        datelistcmd = (
            "grep -Eo '2[0-1][0-9]{2}-[0-1][0-9]-[0-3][0-9]' %s | uniq" % fpath
        )
        datestrlist = subprocess.getoutput(datelistcmd).splitlines()
        return [datetime.strptime(d, "%Y-%m-%d") for d in datestrlist]

    @staticmethod
    def get_count_of_date_in_range(
        datelist: list[datetime], start: datetime, end: datetime
    ) -> int:
        count: int = 0
        for d in datelist:
            if d.date() >= start.date() and d.date() <= end.date():
                count += 1
                continue
        return count

    def get_closest_day_following_end_date(
        self, datelist: list[datetime], end: datetime | None, start: datetime = None
    ):
        def less_than_start(target: datetime, start: datetime | None) -> bool:
            return start and target.date() < start.date()

        if not end:
            return None
        if min(datelist).date() > end.date():
            return None
        near: datetime | None = None
        near_idx: int = 0
        for i, d in enumerate(datelist):
            if not near:
                if less_than_start(d, start=start):
                    continue
                near = d
                near_idx = i
                continue
            if d.date() == end.date():
                near = end
                near_idx = i
                break
            if near.date() < d.date():
                if less_than_start(d, start=start):
                    continue
                if d.date() <= end.date():
                    near = d
                    near_idx = i
                continue
        if not near:
            return near
        if near == datelist[-1]:
            return near
        return datelist[near_idx + 1]

    def get_closest_start_date(
        self,
        datelist: list[datetime],
        start: datetime | None,
        end: datetime | None = None,
    ):
        def greater_than_end(target: datetime, end: datetime | None) -> bool:
            return end and target.date() > end.date()

        if not start:
            return None
        if max(datelist).date() < start.date():
            return None
        near: datetime | None = None
        for d in datelist:
            if start.date() == d.date():
                return start
            if not near:
                if start.date() > d.date():
                    continue
                if greater_than_end(d, end=end):
                    continue
                near = d
                continue
            if near.date() > d.date():
                if greater_than_end(d, end=end):
                    continue
                if d.date() >= start.date():
                    near = d
                    continue
        return near


class ExtractServerLogByCommand(IExtractServerLog):
    def get_list_by_time_period(
        self,
        logname: str,
        start: datetime | None = None,
        end: datetime | None = None,
        loglevel_name_list: list[str] = [],
    ) -> ExtractServerLogResult:
        serverlogfile: ServerLogFile = None
        fpath = cmnlog.getLogPath(logname)
        filename = os.path.basename(fpath)
        if not os.path.isfile(fpath):
            return ExtractServerLogResult(filename=filename, error_msg="not found file")
        if start and end and start > end:
            return ExtractServerLogResult(
                filename=filename, error_msg="date range error"
            )
        cmd = CreateExtractServerLogCommand().get_command(
            fpath=fpath, start=start, end=end, loglevel_name_list=loglevel_name_list
        )
        if cmd:
            retlines = subprocess.getoutput(cmd).splitlines()
            serverlogfile = ServerLogFileFactory.create_by_list(
                textlist=retlines, filename=filename
            )
        if not serverlogfile:
            return ExtractServerLogResult(
                filename=filename, error_msg="can't create log file object"
            )
        if not serverlogfile.logs:
            return ExtractServerLogResult(
                filename=filename, error_msg="no logs to display"
            )
        return ExtractServerLogResult(
            filename=filename,
            text="\n".join(ServerLogRawText().toTextList(logfile=serverlogfile)),
        )

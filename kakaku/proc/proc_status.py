import os
import subprocess
from typing import List, Union

from sqlalchemy.orm import Session

from accessor.server import ProcStatusQuery as psq
from model.server import ProcStatus


class ProcStatusAccess:
    DURING_STARTUP = "DURING_STARTUP"
    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    FAULT = "FAULT"
    NONE = "NONE"

    PS_CMD_HEAD = "ps aux | head -n 1"
    PS_CMD_BODY = "ps aux | grep python | grep -v grep"

    def __init__(self, name: str, pnum: int = 0, myself: bool = True):
        self.pnum: int = pnum
        self.basename: str = name
        self.name: str = f"{self.basename}{self.pnum:02}"
        self.pid: int = -1
        self.status: str = ProcStatusAccess.NONE
        self.isMyself: bool = myself

    def add(self, db: Session, status, pid: Union[int, None] = None) -> None:
        if pid is not None:
            self.pid = pid
        self.checkProcId()
        ps = ProcStatus(proc_id=self.pid, status=status, name=self.name)
        psq.addProcStatus(db, procstses=[ps])

    def update(self, db: Session, status: str) -> None:
        self.checkProcId()
        ps = ProcStatus(name=self.name, proc_id=self.pid, status=status)
        self.status = status
        psq.updateProcStatus(db, procsts=ps)

    def delete(self, db: Session) -> None:
        psq.deleteProcStatuses(db, names=[self.name])

    def getStatus(self) -> str:
        return self.status

    def checkProcId(self) -> None:
        if not self.isMyself:
            return
        if self.pid < 0:
            self.pid = os.getpid()
            return
        ret = ProcStatusAccess.getPsCommand()
        pids = [int(r["PID"]) for r in ret]
        MAX = 1
        for c in range(MAX):
            if self.pid in pids:
                return
            else:
                self.pid = os.getpid()

    @staticmethod
    def get_all(db: Session) -> List:
        return psq.getAllProcStatuses(db)

    @staticmethod
    def delete_all(db: Session) -> None:
        psq.deleteAllProcStatuses(db)

    @staticmethod
    def getPsCommand() -> List:
        head = subprocess.getoutput(ProcStatusAccess.PS_CMD_HEAD).split()
        retlines = subprocess.getoutput(ProcStatusAccess.PS_CMD_BODY).splitlines()
        ret = []
        for line in retlines:
            values = line.split()
            if len(head) < len(values):
                values[len(head) - 1] = values[len(head) - 1 :]
            ret.append(dict(zip(head, values)))
        return ret


class ProcName:
    MANAGER = "scrapingmanage"
    DOWNLOAD = "dlproc"
    PARSE = "htmlparse"

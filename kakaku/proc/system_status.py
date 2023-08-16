
from typing import List

from sqlalchemy.orm import Session
from proc.proc_status import ProcStatusAccess

from enum import Enum

class SystemStatus(Enum):
    NONE = 0
    DURING_STARTUP = 1
    ACTIVE = 2
    DATA_UPDATE = 3
    FAULT = 4
    STOP = 5

class SystemStatusToJName:
    toJnameTable = {
        SystemStatus.NONE.name:"不明",
        SystemStatus.DURING_STARTUP.name:"起動中",
        SystemStatus.ACTIVE.name:"稼働中",
        SystemStatus.DATA_UPDATE.name:"更新中",
        SystemStatus.FAULT.name:"エラー",
        SystemStatus.STOP.name:"停止",
    }
    @classmethod
    def get_jname(cls, sts :str) -> str:
        return cls.toJnameTable[sts]

class SystemStatusAccess:

    def __init__(self):
        self.proclist = []
        self.proc_ids = []
        self.system_status = SystemStatus.NONE
    
    def getStatus(self) -> SystemStatus:
        return self.system_status
    
    def update(self, db :Session) -> None:
        self.proclist = ProcStatusAccess.get_all(db)

        for procsts in self.proclist:
            self.proc_ids.append(procsts.proc_id)
        
        #DB登録なし
        if len(self.proc_ids) == 0:
            self.system_status = SystemStatus.STOP
            return
        
        #起動しているプロセスなし
        psret = ProcStatusAccess.getPsCommand()
        if len(psret) == 0 or SystemStatusAccess.isProcStop(self.proc_ids, psret):
            self.system_status = SystemStatus.STOP
            return
        
        #ゾンビ
        isdef, psret = SystemStatusAccess.isProcDefunct(self.proc_ids, psret)
        if isdef:
            self.system_status = SystemStatus.FAULT
            return
        
        cur_sts = SystemStatus.NONE
        for procsts in self.proclist:
            if procsts.status == ProcStatusAccess.FAULT:
                cur_sts = self.getPriorityStatus(cur_sts, SystemStatus.FAULT)
                break
            
            if procsts.status == ProcStatusAccess.ACTIVE:
                cur_sts = self.getPriorityStatus(cur_sts, SystemStatus.DATA_UPDATE)
                continue

            if procsts.status == ProcStatusAccess.WAITING:
                cur_sts = self.getPriorityStatus(cur_sts, SystemStatus.ACTIVE)
                continue

            if procsts.status == ProcStatusAccess.DURING_STARTUP:
                cur_sts = self.getPriorityStatus(cur_sts, SystemStatus.DURING_STARTUP)
                continue
        
        self.system_status = cur_sts
        return

    @staticmethod
    def getPriorityStatus(cur_sts: SystemStatus,
                        next_sts: SystemStatus
                        ) -> SystemStatus:
        if next_sts.value > cur_sts.value:
            return next_sts
        return cur_sts
    
    @staticmethod
    def isProcDefunct(pids: List
                      ,psret: List
                      ):
        for proc in psret:
            if int(proc["PID"]) in pids:
                for stat in proc["STAT"]:
                    if stat == "Z":
                        return True, proc
        return False, None

    @staticmethod
    def isProcStop(pids, psret) -> bool:
        for pid in pids:
            for proc in psret:
                if int(proc["PID"]) == pid:
                    return False
        return True

from typing import List
from datetime import datetime
from .read_sqlalchemy import getSession

from model.server import (
    ProcStatus,
    ProcStatusLog,
    OrganizeLog,
)
from sqlalchemy import (
    select,
    delete,
    update,
)
class ProcStatusQuery:
    @staticmethod
    def getProcStatuses(names: List) -> List:
        ses = getSession()
        stmt = select(ProcStatus).where(ProcStatus.name.in_(names))
        return ses.execute(stmt).all()
    
    @staticmethod
    def getAllProcStatuses() -> List:
        ses = getSession()
        stmt = select(ProcStatus)
        return ses.scalars(stmt).all()
    
    @staticmethod
    def addProcStatus(procstses: List) -> None:
        ses = getSession()
        ses.add_all(procstses)
        ses.commit()

    @staticmethod
    def deleteProcStatuses(names: List) -> None:
        ses = getSession()
        stmt = delete(ProcStatus).where(ProcStatus.name.in_(names))
        ses.execute(stmt)
        ses.commit()

    @staticmethod
    def deleteAllProcStatuses() -> None:
        ses = getSession()
        stmt = delete(ProcStatus)
        ses.execute(stmt)
        ses.commit()

    @staticmethod
    def updateProcStatus(procsts: ProcStatus) -> None:
        ses = getSession()
        stmt = ( update(ProcStatus)
                .where(ProcStatus.name==procsts.name)
                .values(status=procsts.status, proc_id=procsts.proc_id)
                )
        ses.execute(stmt)
        ses.commit()

class OrganizeLogQuery:
    @staticmethod
    def add_log(name :str, status :str):
        ses = getSession()
        is_log = ( select(OrganizeLog)
                  .where(OrganizeLog.name == name)
                  )
        log = ses.scalar(is_log)
        if log:
            log.status = status
            log.created_at = datetime.utcnow()
        else:
            ses.add(OrganizeLog(name=name, status=status))
        ses.commit()
        ses.close()
    
    @staticmethod
    def get_log(name :str):
        stmt = ( select(OrganizeLog)
                .where(OrganizeLog.name == name)
                )
        ses = getSession()
        ret = ses.scalar(stmt)
        return ret

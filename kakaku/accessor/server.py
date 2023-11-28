from typing import List
from datetime import datetime

from model.server import (
    ProcStatus,
    ProcStatusLog,
    OrganizeLog,
    AutoUpdateSchedule,
)
from sqlalchemy import (
    select,
    delete,
    update,
)
from sqlalchemy.orm import Session

class ProcStatusQuery:
    @staticmethod
    def getProcStatuses(db :Session, names: List) -> List:
        stmt = select(ProcStatus).where(ProcStatus.name.in_(names))
        return db.execute(stmt).all()
    
    @staticmethod
    def getAllProcStatuses(db :Session) -> List:
        stmt = select(ProcStatus)
        return db.scalars(stmt).all()
    
    @staticmethod
    def addProcStatus(db :Session, procstses: List[ProcStatus]) -> None:
        db.add_all(procstses)
        db.commit()
        for proc in procstses:
            db.refresh(proc)

    @staticmethod
    def deleteProcStatuses(db :Session, names: List) -> None:
        stmt = delete(ProcStatus).where(ProcStatus.name.in_(names))
        db.execute(stmt)
        db.commit()

    @staticmethod
    def deleteAllProcStatuses(db :Session) -> None:
        stmt = delete(ProcStatus)
        db.execute(stmt)
        db.commit()

    @staticmethod
    def updateProcStatus(db :Session, procsts: ProcStatus) -> None:
        stmt = ( update(ProcStatus)
                .where(ProcStatus.name==procsts.name)
                .values(status=procsts.status, proc_id=procsts.proc_id)
                )
        db.execute(stmt)
        db.commit()

class OrganizeLogQuery:
    @staticmethod
    def add_log(db :Session, name :str, status :str):
        is_log = ( select(OrganizeLog)
                  .where(OrganizeLog.name == name)
                  )
        log = db.scalar(is_log)
        if log:
            log.status = status
            log.created_at = datetime.utcnow()
        else:
            db.add(OrganizeLog(name=name, status=status))
            db.commit()
    
    @staticmethod
    def get_log(db :Session, name :str):
        stmt = ( select(OrganizeLog)
                .where(OrganizeLog.name == name)
                )
        return db.scalar(stmt)

class AutoUpdateScheduleQuery:
    @classmethod
    def init_schedules(cls, db :Session, requirements :list[AutoUpdateSchedule]):
        cls.delete_schedules(db)
        if len(requirements) == 0:
            return
        db.add_all(requirements)
        db.commit()
    
    @classmethod
    def update_status(cls, db :Session, requirements :list[AutoUpdateSchedule]):
        if len(requirements) == 0:
            return
        for req in requirements:
            stmt = ( update(AutoUpdateSchedule)
                    .where(AutoUpdateSchedule.requirement == req.requirement)
                    .values(status=req.status)
                    )
            db.execute(stmt)
        db.commit()
        
    @staticmethod
    def get_schedules(db :Session):
        stmt = ( select(AutoUpdateSchedule)
                .order_by(AutoUpdateSchedule.requirement.asc())
                )
        return db.scalars(stmt).all()
    
    @staticmethod
    def delete_schedules(db :Session):
        stmt = ( delete(AutoUpdateSchedule) )
        db.execute(stmt)
        db.commit()
from datetime import datetime, timezone

from model.server import (
    DBVersion,
    ProcStatus,
    OrganizeLog,
    AutoUpdateSchedule,
    SystemStatusLog,
)
from sqlalchemy import (
    select,
    delete,
    update,
    func,
    between,
)
from sqlalchemy.orm import Session
from accessor.util import (
    utc_to_jst_datetime_for_query,
)


class ProcStatusQuery:
    @staticmethod
    def getProcStatuses(db: Session, names: list) -> list:
        stmt = select(ProcStatus).where(ProcStatus.name.in_(names))
        return db.execute(stmt).all()

    @staticmethod
    def getAllProcStatuses(db: Session) -> list:
        stmt = select(ProcStatus)
        return db.scalars(stmt).all()

    @staticmethod
    def addProcStatus(db: Session, procstses: list[ProcStatus]) -> None:
        db.add_all(procstses)
        db.commit()
        for proc in procstses:
            db.refresh(proc)

    @staticmethod
    def deleteProcStatuses(db: Session, names: list) -> None:
        stmt = delete(ProcStatus).where(ProcStatus.name.in_(names))
        db.execute(stmt)
        db.commit()

    @staticmethod
    def deleteAllProcStatuses(db: Session) -> None:
        stmt = delete(ProcStatus)
        db.execute(stmt)
        db.commit()

    @staticmethod
    def updateProcStatus(db: Session, procsts: ProcStatus) -> None:
        stmt = (
            update(ProcStatus)
            .where(ProcStatus.name == procsts.name)
            .values(status=procsts.status, proc_id=procsts.proc_id)
        )
        db.execute(stmt)
        db.commit()


class OrganizeLogQuery:
    @staticmethod
    def add_log(db: Session, name: str, status: str):
        is_log = select(OrganizeLog).where(OrganizeLog.name == name)
        log = db.scalar(is_log)
        if log:
            log.status = status
            log.created_at = datetime.now(timezone.utc)
        else:
            db.add(OrganizeLog(name=name, status=status))
            db.commit()

    @staticmethod
    def get_log(db: Session, name: str):
        stmt = select(OrganizeLog).where(OrganizeLog.name == name)
        return db.scalar(stmt)


class AutoUpdateScheduleQuery:
    @classmethod
    def init_schedules(cls, db: Session, requirements: list[AutoUpdateSchedule]):
        cls.delete_schedules(db)
        if len(requirements) == 0:
            return
        db.add_all(requirements)
        db.commit()

    @classmethod
    def update_status(cls, db: Session, requirements: list[AutoUpdateSchedule]):
        if len(requirements) == 0:
            return
        for req in requirements:
            stmt = (
                update(AutoUpdateSchedule)
                .where(AutoUpdateSchedule.requirement == req.requirement)
                .values(status=req.status)
            )
            db.execute(stmt)
        db.commit()

    @staticmethod
    def get_schedules(db: Session):
        stmt = select(AutoUpdateSchedule).order_by(AutoUpdateSchedule.requirement.asc())
        return db.scalars(stmt).all()

    @staticmethod
    def delete_schedules(db: Session):
        stmt = delete(AutoUpdateSchedule)
        db.execute(stmt)
        db.commit()


class DBVersionQuery:
    @classmethod
    def get_version(cls, db: Session):
        stmt = select(DBVersion)
        return db.scalar(stmt)

    @classmethod
    def set_version(cls, db: Session, new_v: DBVersion):
        v = cls.get_version(db)
        if v:
            stmt = (
                update(DBVersion)
                .where(DBVersion.id == v.id)
                .values(major=new_v.major, minor=new_v.minor, patch=new_v.patch)
            )
            db.excute(stmt)
            db.commit()
            return
        db.add(new_v)
        db.commit()
        db.refresh(new_v)


class SystemStatusLogQuery:
    @classmethod
    def add(cls, db: Session, status: str):
        syssts = SystemStatusLog(status=status)
        db.add(syssts)
        db.commit()
        db.refresh(syssts)

    @classmethod
    def add_check_pre_status(cls, db: Session, status: str):
        newest = cls.get_newest_log(db)
        if newest and newest.status == status:
            return
        cls.add(db=db, status=status)

    @classmethod
    def get_newest_log(cls, db: Session):
        stmt = (
            select(SystemStatusLog)
            .order_by(SystemStatusLog.created_at.desc(), SystemStatusLog.log_id.desc())
            .limit(1)
        )
        return db.scalar(stmt)

    @classmethod
    def get_all(cls, db: Session) -> SystemStatusLog | None:
        stmt = select(SystemStatusLog).order_by(
            SystemStatusLog.created_at.desc(), SystemStatusLog.log_id.desc()
        )
        return db.scalars(stmt).all()

    @classmethod
    def get_count_log(cls, db: Session):
        stmt = select(func.count(SystemStatusLog.log_id))
        return db.scalar(stmt)

    @classmethod
    def get_old_log(cls, db: Session, limit=-1):
        stmt = select(SystemStatusLog).order_by(
            SystemStatusLog.created_at.asc(), SystemStatusLog.log_id.asc()
        )
        if limit > 0:
            stmt = stmt.limit(limit)
        return db.scalars(stmt).all()

    @classmethod
    def get_count_by_systemstatus_and_datetime_range(
        cls, db: Session, status_list: list[str], start: datetime, end: datetime
    ):
        start_n = start.replace(tzinfo=None)
        end_n = end.replace(tzinfo=None)
        stmt = (
            select(func.count(SystemStatusLog.log_id))
            .where(SystemStatusLog.status.in_(status_list))
            .where(
                between(
                    utc_to_jst_datetime_for_query(SystemStatusLog.created_at),
                    start_n,
                    end_n,
                )
            )
        )
        return db.scalar(stmt)

    @classmethod
    def delete_amount_over_limit(cls, db: Session, limit: int):
        elem_cnt = cls.get_count_log(db)
        if limit >= elem_cnt:
            return
        del_cnt = elem_cnt - limit
        del_targets = cls.get_old_log(db=db, limit=del_cnt)
        del_target_ids = [t.log_id for t in del_targets]
        stmt = delete(SystemStatusLog).where(SystemStatusLog.log_id.in_(del_target_ids))
        db.execute(stmt)
        db.commit()

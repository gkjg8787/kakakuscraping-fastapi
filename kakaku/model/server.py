from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    def toDict(self):
        dic = {}
        for col in self.__table__.columns:
            dic[col.name] = getattr(self, col.name)
        return dic


class DBVersion(Base):
    __tablename__ = "db_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    major: Mapped[int]
    minor: Mapped[int]
    patch: Mapped[int]

    def __repr__(self) -> str:
        return (
            "ProcStatus("
            f"id={self.id!r}"
            f", major={self.major!r}"
            f", minor={self.minor!r}"
            f", patch={self.patch!r}"
            ")"
        )


class ProcStatus(Base):
    __tablename__ = "proc_status"

    num_id: Mapped[int] = mapped_column(primary_key=True)
    proc_id: Mapped[int]
    name: Mapped[str]
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP()
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP(),
        onupdate=func.CURRENT_TIMESTAMP(),
        server_onupdate=func.CURRENT_TIMESTAMP(),
    )

    def __repr__(self) -> str:
        return (
            "ProcStatus("
            f"num_id={self.num_id!r}"
            f", proc_id={self.proc_id!r}"
            f", name={self.name!r}"
            f", status={self.status!r}"
            f", created_at={self.created_at!r}"
            f", updated_at={self.updated_at!r}"
            ")"
        )


class SystemStatusLog(Base):
    __tablename__ = "system_status_log"

    log_id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP()
    )

    def __repr__(self) -> str:
        return (
            "SystemStatusLog("
            f"log_id={self.log_id!r}"
            f", status={self.status!r}"
            f", created_at={self.created_at!r}"
            ")"
        )


class OrganizeLog(Base):
    __tablename__ = "organizelog"

    log_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP()
    )

    def __repr__(self) -> str:
        return (
            "OrganizeLog("
            f"log_id={self.log_id!r}"
            f", name={self.name!r}"
            f", status={self.status!r}"
            f", created_at={self.created_at!r}"
            ")"
        )


class AutoUpdateSchedule(Base):
    __tablename__ = "autoupdateschedule"

    id: Mapped[int] = mapped_column(primary_key=True)
    requirement: Mapped[str]
    status: Mapped[str]
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP()
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP(),
        onupdate=func.CURRENT_TIMESTAMP(),
        server_onupdate=func.CURRENT_TIMESTAMP(),
    )

    def __repr__(self) -> str:
        return (
            "AutoUpdateSchedule("
            f"id={self.id!r}"
            f", requirement={self.requirement!r}"
            f", status={self.status!r}"
            f", updated_at={self.updated_at!r}"
            f", created_at={self.created_at!r}"
            ")"
        )

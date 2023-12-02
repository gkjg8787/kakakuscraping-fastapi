
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

    id : Mapped[int] = mapped_column(primary_key=True)
    major : Mapped[int]
    minor : Mapped[int]
    patch : Mapped[int]

class ProcStatus(Base):
    __tablename__ = "proc_status"

    num_id : Mapped[int] = mapped_column(primary_key=True)
    proc_id : Mapped[int] 
    name : Mapped[str]
    status : Mapped[str]
    created_at : Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())
    updated_at : Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP()
        ,onupdate=func.CURRENT_TIMESTAMP()
        ,server_onupdate=func.CURRENT_TIMESTAMP()
        )

    def __repr__(self) -> str:
        return ( f"ProcStatus(num_id={self.num_id!r}, proc_id={self.proc_id!r}, name={self.name!r}, status={self.status!r}"
                            f", created_at={self.created_at!r}, updated_at={self.updated_at!r}"
                            ")" )

class SystemStatusLog(Base):
    __tablename__ = "system_status_log"

    log_id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    def __repr__(self) -> str:
        return ( f"SystemStatusLog(log_id={self.log_id!r}, status={self.status!r}, created_at={self.created_at!r}")

class OrganizeLog(Base):
    __tablename__ = "organizelog"

    log_id :Mapped[int] = mapped_column(primary_key=True)
    name :Mapped[str]
    status :Mapped[str]
    created_at :Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    def __repr__(self) -> str:
        return ( f"OrganizeLog(log_id={self.log_id!r}, name={self.name!r}, status={self.status!r}, created_at={self.created_at!r}")

class AutoUpdateSchedule(Base):
    __tablename__ = "autoupdateschedule"

    id :Mapped[int] = mapped_column(primary_key=True)
    requirement :Mapped[str]
    status :Mapped[str]
    updated_at :Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())
    created_at :Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP()
        ,onupdate=func.CURRENT_TIMESTAMP()
        ,server_onupdate=func.CURRENT_TIMESTAMP()
        )
    
    def __repr__(self) -> str:
        return ( f"AutoUpdateSchedule(id~{self.id!r}, requirement={self.requirement!r}, status={self.status!r}"
                 f", updated_at={self.updated_at!r}, created_at={self.created_at!r}"
                 ")")
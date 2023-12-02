from enum import Enum

from sqlalchemy.orm import Session

from accessor.server import SystemStatusLogQuery
from common.read_config import get_system_status_log_max

from proc import system_status

def update_to_active_for_systemstatuslog(db :Session):
    ssa = system_status.SystemStatusAccess()
    ssa.update(db)
    if ssa.getStatus() == system_status.SystemStatus.ACTIVE:
        SystemStatusLogAccess.add_check_pre_status(db=db, sysstslog=SystemStatusLogName.ACTIVE)

class SystemStatusLogName(Enum):
    NONE = (0, "")
    STARTUP = (1, "起動")
    ACTIVE = (2, "稼働中")
    DATA_UPDATE = (3, "更新")
    FAULT = (4, "エラー")
    STOP = (5, "停止")
    DB_ORGANIZE = (6, "データベース整理")
    ALL_DATA_UPDATE = (7, "一括更新")

    def __init__(self, id:int, text :str):
        self.id = id
        self.jtext = text

class SystemStatusLogAccess:

    @classmethod
    def add(cls, db :Session, sysstslog :SystemStatusLogName):
        SystemStatusLogQuery.add(db=db, status=sysstslog.jtext)
        SystemStatusLogQuery.delete_amount_over_limit(db=db, limit=get_system_status_log_max())
    
    @classmethod
    def add_check_pre_status(cls, db :Session, sysstslog :SystemStatusLogName):
        SystemStatusLogQuery.add_check_pre_status(db=db, status=sysstslog.jtext)
        SystemStatusLogQuery.delete_amount_over_limit(db=db, limit=get_system_status_log_max())

    @classmethod
    def get_all(cls, db :Session):
        return SystemStatusLogQuery.get_all(db=db)
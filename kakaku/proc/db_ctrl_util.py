from enum import Enum
from sqlalchemy import (
    inspect,
    MetaData,
    Table,
)
from model import (
    item,
    store,
    server,
)
from accessor.read_sqlalchemy import (
    getEngine,
    get_old_db_engine,
    get_session,
)
from accessor.server import DBVersionQuery
from common.read_config import get_db_version


def getNewDBVersion():
    v = get_db_version()
    return server.DBVersion(major=v[0], minor=v[1], patch=v[2])


def setNewDBVersion():
    with next(get_session()) as db:
        DBVersionQuery.set_version(db=db, new_v=getNewDBVersion())


def existTable(tablename: str):
    if inspect(getEngine()).has_table(tablename):
        return True
    return False


def isNoVersion():
    if existTable(server.DBVersion.__tablename__):
        with next(get_session()) as db:
            v = DBVersionQuery.get_version(db=db)
            if not v:
                return True
        return False
    return True


def remove_unnecessaryTable(tablename: str):
    meta = MetaData()
    table = Table(tablename, meta)
    table.drop(bind=getEngine())


def checkNoVersion():
    unnecessary_table = "proc_status_log"
    if isNoVersion():
        if existTable(unnecessary_table):
            remove_unnecessaryTable(unnecessary_table)
        setNewDBVersion()
        return True
    return False


def checkDBVersion():
    if checkNoVersion():
        return


def createDB():
    print("create all table")
    eng = getEngine()
    item.Base.metadata.create_all(eng)
    store.Base.metadata.create_all(eng)
    server.Base.metadata.create_all(eng)

    old_db_eng = get_old_db_engine()
    item.Base.metadata.create_all(old_db_eng)

    checkDBVersion()


def removeDB():
    print("drop all table")
    eng = getEngine()
    item.Base.metadata.drop_all(eng)
    store.Base.metadata.drop_all(eng)
    server.Base.metadata.drop_all(eng)


class DBCommandName(Enum):
    CREATE = "create"
    DROP = "drop"
    RECREATE = "recreate"

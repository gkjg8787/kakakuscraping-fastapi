from typing import Union
from enum import Enum
from sqlalchemy import event
from sqlalchemy import exc
import os
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy.pool import NullPool

from common import read_config

dbconf = read_config.get_databases()
url_obj = URL.create(**dbconf["default"])
is_echo = dbconf["is_echo"]
engine = create_engine(url_obj, echo=is_echo)
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


class DBName(Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


def __get_target_dbconf(settingname: Union[str, None] = None):
    if settingname is None:
        return dbconf["default"]
    if "default" == settingname or "old_db" == settingname:
        return dbconf[settingname]


def is_sqlite(settingname: Union[str, None] = None):
    targetconf = __get_target_dbconf(settingname)
    if "drivername" in targetconf and DBName.SQLITE.value in targetconf["drivername"]:
        return True
    return False


def is_postgre(settingname: Union[str, None] = None):
    targetconf = __get_target_dbconf(settingname)
    if (
        "drivername" in targetconf
        and DBName.POSTGRESQL.value in targetconf["drivername"]
    ):
        return True
    return False


def getEngine():
    return engine


def get_session():
    ses = SessionLocal()
    try:
        yield ses
    finally:
        ses.close()


def get_old_db_engine():
    return create_engine(
        URL.create(**dbconf["old_db"]), echo=is_echo, poolclass=NullPool
    )


def get_old_db_session():
    old_db_ses = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=get_old_db_engine())
    )
    ses = old_db_ses()
    try:
        yield ses
    finally:
        ses.close()


@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    connection_record.info["pid"] = os.getpid()


@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    pid = os.getpid()
    if connection_record.info["pid"] != pid:
        connection_record.dbapi_connection = connection_proxy.dbapi_connection = None
        raise exc.DisconnectionError(
            "Connection record belongs to pid %s, "
            "attempting to check out in pid %s" % (connection_record.info["pid"], pid)
        )

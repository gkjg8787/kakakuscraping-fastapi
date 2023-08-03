from typing import Union
from enum import Enum
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from common import read_config

dbconf = read_config.get_databases()
url_obj = URL.create(**dbconf['default'])
is_echo = dbconf['is_echo']
engine = create_engine(url_obj, echo=is_echo, poolclass=NullPool)

class DBName(Enum):
    SQLITE = 'sqlite'
    POSTGRESQL = 'postgresql'

def __get_target_dbconf(settingname :Union[str, None] = None):
    if settingname is None:
        return dbconf['default']
    if 'default' == settingname \
        or 'old_db' == settingname:
        return dbconf[settingname]

def is_sqlite(settingname :Union[str, None] = None):
    targetconf = __get_target_dbconf(settingname)
    if 'drivername' in targetconf\
        and DBName.SQLITE.value in targetconf['drivername']:
        return True
    return False

def is_postgre(settingname :Union[str, None] = None):
    targetconf = __get_target_dbconf(settingname)
    if 'drivername' in targetconf\
        and DBName.POSTGRESQL.value in targetconf['drivername']:
        return True
    return False

def getEngine():
    return engine

def getSession():
    return Session(getEngine())

def get_old_db_engine():
    return create_engine(URL.create(**dbconf['old_db']), echo=is_echo, poolclass=NullPool)

def get_old_db_session():
    return Session(get_old_db_engine())

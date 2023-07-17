from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from common import read_config

dbconf = read_config.get_databases()
url_obj = URL.create(**dbconf['default'])
is_echo = dbconf['is_echo']
engine = create_engine(url_obj, echo=is_echo, poolclass=NullPool)

def getEngine():
    return engine

def getSession():
    return Session(getEngine())

def get_old_db_engine():
    return create_engine(URL.create(**dbconf['old_db']), echo=is_echo, poolclass=NullPool)

def get_old_db_session():
    return Session(get_old_db_engine())

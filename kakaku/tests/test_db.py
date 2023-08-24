import os
import pytest
from uuid import uuid4

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy.orm.session import close_all_sessions
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy_utils import (
    create_database as cdb,
    drop_database as ddb,
    database_exists,
)

from model import (
    item,
    server,
    store,
)
from accessor.read_sqlalchemy import get_session
from main import app

import settings

DATABASES = {
    "default":{
        "drivername":"sqlite",
        "database":f"{settings.BASE_DIR}/db/test.sqlite",
    },
    "old_db":{
        "drivername":"sqlite",
        "database":f"{settings.BASE_DIR}/db/test_old.sqlite",
    },
    "postgre_default":{
        "drivername":"postgresql+psycopg2",
        "username":"dbuser",
        "password":"posgre134",
        "host":"postgres",
        "database":"testdb",
        "port":"5432",
    },
    "postgre_old_db":{
        "drivername":"postgresql+psycopg2",
        "username":"dbuser",
        "password":"posgre134",
        "host":"postgres",
        "database":"testolddb",
        "port":"5432",
    },
    "is_echo":False
}


@pytest.fixture(scope="function")
def test_db():
    TEST_DB_URL = URL.create(**DATABASES['default'])
    is_echo = DATABASES['is_echo']
    engine = create_engine(TEST_DB_URL, echo=is_echo)
    item.Base.metadata.create_all(bind=engine)
    server.Base.metadata.create_all(bind=engine)
    store.Base.metadata.create_all(bind=engine)
    TEST_OLD_DB_URL = URL.create(**DATABASES['old_db'])
    old_eng = create_engine(TEST_OLD_DB_URL, echo=is_echo)
    item.Base.metadata.create_all(bind=old_eng)


    function_scope = uuid4().hex
    TestingSessionLocal = scoped_session(
        sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        ),
        scopefunc=lambda: function_scope,
    )
    
    def get_db_for_testing():
        db = TestingSessionLocal()
        try:
            yield db
            db.commit()
        except SQLAlchemyError:
            db.rollback()

    #　テスト時に依存するDBを本番用からテスト用のものに切り替える 
    app.dependency_overrides[get_session] = get_db_for_testing
    yield TestingSessionLocal()
    
    TestingSessionLocal.remove()
    close_all_sessions()
    # セッション終了後にengineを破棄し、DBの状態を初期化する
    engine.dispose()

def drop_test_db():
    TEST_DB_URL = URL.create(**DATABASES['default'])
    is_echo = DATABASES['is_echo']
    engine = create_engine(TEST_DB_URL, echo=is_echo)
    item.Base.metadata.drop_all(bind=engine)
    server.Base.metadata.drop_all(bind=engine)
    store.Base.metadata.drop_all(bind=engine)
    TEST_OLD_DB_URL = URL.create(**DATABASES['old_db'])
    old_eng = create_engine(TEST_OLD_DB_URL, echo=is_echo)
    item.Base.metadata.drop_all(bind=old_eng)

def create_database():
    if 'sqlite' in DATABASES['default']['drivername']:
        return
    def create_database_func(dbkey):
        engine_url = URL.create(**DATABASES[dbkey])
        if database_exists(engine_url):
            return
        cdb(engine_url)
    create_database_func('default')
    create_database_func('old_db')

def drop_database():
    if 'sqlite' in DATABASES['default']['drivername']:
        os.remove(DATABASES['default']['database'])
        os.remove(DATABASES['old_db']['database'])
        return
    def drop_database_func(dbkey):
        engine_url = URL.create(**DATABASES[dbkey])
        if not database_exists(engine_url):
            return
        ddb(engine_url)

    drop_database_func('default')
    drop_database_func('old_db')
import sys
import argparse
from enum import Enum

from model import item, store, server
from accessor.read_sqlalchemy import getEngine, get_old_db_engine

def createDB():
    print("create all table")
    eng = getEngine()
    item.Base.metadata.create_all(eng)
    store.Base.metadata.create_all(eng)
    server.Base.metadata.create_all(eng)
    
    old_db_eng = get_old_db_engine()
    item.Base.metadata.create_all(old_db_eng)

def removeDB():
    print("drop all table")
    eng = getEngine()
    item.Base.metadata.drop_all(eng)
    store.Base.metadata.drop_all(eng)
    server.Base.metadata.drop_all(eng)


class DBCommandName(Enum):
    CREATE = 'create'
    DROP = 'drop'
    RECREATE = 'recreate'

def parse_paramter(argv):
    parser = argparse.ArgumentParser(description='table create and drop')
    parser.add_argument('name', type=str, choices=[v.value for v in DBCommandName])
    
    args = parser.parse_args(argv[1:])
    return args

def main(argv):
    param = parse_paramter(argv)
    if param.name == DBCommandName.RECREATE.value:
        removeDB()
        createDB()
        return
    if param.name == DBCommandName.CREATE.value:
        createDB()
        return
    if param.name == DBCommandName.DROP.value:
        removeDB()
        return
    return

if __name__ == '__main__':
    main(sys.argv)
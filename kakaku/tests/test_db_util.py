import sys
import argparse
from enum import Enum

from os.path import dirname
parent_dir = dirname(dirname(__file__))
sys.path.append(parent_dir)

from tests.test_db import create_database, drop_database


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
        drop_database()
        create_database()
        return
    if param.name == DBCommandName.CREATE.value:
        create_database()
        return
    if param.name == DBCommandName.DROP.value:
        drop_database()
        return
    return

if __name__ == '__main__':
    main(sys.argv)
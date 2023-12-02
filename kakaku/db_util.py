import sys
import argparse


from proc.db_ctrl_util import (
    DBCommandName,
    createDB,
    removeDB,
)

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
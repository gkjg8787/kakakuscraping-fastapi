import sys
import argparse
import json
import datetime

from sqlalchemy.orm import Session
from accessor.read_sqlalchemy import get_session

from proc.proc_status import ProcStatusAccess
from proc.system_status import SystemStatusAccess

def getSystemStatus(db :Session):
    ssa = SystemStatusAccess()
    ssa.update(db)
    return ssa.getStatus().name

def getProcStatus(db :Session):
    pstses = ProcStatusAccess.get_all(db)
    rets = []
    for psts in pstses:
        rets.append(psts.toDict())
    return rets

def parseParamOpt(argv):
    parser = argparse.ArgumentParser(description='get system status or process status')
    parser.add_argument('-s', '--system', help='system status', action='store_true')
    parser.add_argument('-p', '--proc', help='system status', action='store_true')
    args = parser.parse_args(argv)
    #print(args)
    return args

def json_serial(obj):
    if isinstance(obj, (datetime.datetime)):
        return obj.isoformat()
    # 上記以外はサポート対象外.
    raise TypeError ("Type %s not serializable" % type(obj))

def main(argv):
    args = parseParamOpt(argv[1:])
    db = next(get_session())
    ret = {}
    if args.system:
        ret["SystemStatus"] = getSystemStatus(db)
    if args.proc:
        ret["ProcStatus"] = getProcStatus(db)
    if len(ret) > 0:
        print(json.dumps(ret, default=json_serial))

if __name__ == "__main__":
    main(sys.argv)
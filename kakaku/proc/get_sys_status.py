import sys
import argparse
import json
import datetime

from proc.proc_status import ProcStatusAccess
from proc.system_status import SystemStatusAccess

def getSystemStatus():
    ssa = SystemStatusAccess()
    ssa.update()
    return ssa.getStatus().name

def getProcStatus():
    pstses = ProcStatusAccess.get_all()
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
    ret = {}
    if args.system:
        ret["SystemStatus"] = getSystemStatus()
    if args.proc:
        ret["ProcStatus"] = getProcStatus()
    if len(ret) > 0:
        print(json.dumps(ret, default=json_serial))

if __name__ == "__main__":
    main(sys.argv)
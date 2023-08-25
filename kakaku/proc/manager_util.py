import os

from sqlalchemy.orm import Session
from proc.proc_status import ProcStatusAccess


def getProcStatusAccess(pnum :int, name :str):
    psa = ProcStatusAccess(name, pnum)
    return psa

def writeProcFault(db :Session, psa :ProcStatusAccess):
    if psa.getStatus() == ProcStatusAccess.FAULT:
        return
    psa.update(db, status=ProcStatusAccess.FAULT)
    return psa

def writeProcActive(db :Session, psa :ProcStatusAccess):
    if psa.getStatus() == ProcStatusAccess.ACTIVE:
        return
    psa.update(db, status=ProcStatusAccess.ACTIVE)
    return psa

def writeProcWaiting(db :Session, psa :ProcStatusAccess):
    if psa.getStatus() == ProcStatusAccess.WAITING:
        return
    psa.update(db, status=ProcStatusAccess.WAITING)
    return psa

def writeProcStart(db :Session, pnum :int, name :str):
    psa :ProcStatusAccess = getProcStatusAccess(pnum=pnum, name=name)
    psa.add(db, status=ProcStatusAccess.DURING_STARTUP, pid=os.getpid())
    return psa
import os
import time
import sys
import queue


from proc import sendcmd
from proc import updateAllItems

from common import cmnlog, util
from proc.dlmanage import DlProc
from proc.parsemanage import ParseProc
from proc.proc_status import ProcStatusAccess, ProcName
from proc.system_status_log import (
    SystemStatusLogAccess,
    SystemStatusLogName,
    update_to_active_for_systemstatuslog,
)
from proc import manager_util

from accessor.read_sqlalchemy import get_session, Session

from common.read_config import (
    get_back_server_queue_timeout,
)
from accessor.server import OrganizeLogQuery
from proc import (
    db_organizer,
    online_store_postage
)

from proc.auto_update import TimerProc

from .queuemanager import (
    QueueManager,
    server_port,
    server_pswd,
)
from itemcomb.prefecture import PrefectureDBSetting

QUEUE_TIMEOUT = int(get_back_server_queue_timeout()) #5


dlproc :DlProc | None = None
parseproc :ParseProc | None = None
timerproc :TimerProc | None = None


def getProcStatusAccess():
    return ProcStatusAccess(name=ProcName.MANAGER)

def writeAllProcStop(db :Session):
    ProcStatusAccess.delete_all(db)

def writeProcStart(db :Session, psa :ProcStatusAccess | None = None):
    writeAllProcStop(db)
    if psa is None :
        psa = getProcStatusAccess()
    psa.add(db, status=ProcStatusAccess.DURING_STARTUP, pid=os.getpid())
    return psa

def get_filename():
    return os.path.basename(__file__)

def getLogger(logfn):
    return cmnlog.getLogger(logfn)

def startQueue():
    cmnlog.initProcessLogger()
    logger = getLogger(cmnlog.LogName.MANAGER)
    logger.info(get_filename() + ' manager start')
    with next(get_session()) as db:
        writeProcStart(db=db)
        SystemStatusLogAccess.add(db=db, sysstslog=SystemStatusLogName.STARTUP)

    task_queue = queue.Queue()
    result_queue = queue.Queue()

    QueueManager.register('get_task_queue', callable=lambda: task_queue)
    QueueManager.register('get_result_queue', callable=lambda: result_queue)

    manager = QueueManager(address=('', server_port), authkey=server_pswd)
    manager.start()
    task = manager.get_task_queue()
    result = manager.get_result_queue()

    createSubProc()
    waitTask(task=task, result=result)

    endSubProc()
    with next(get_session()) as db:
        writeAllProcStop(db=db)
        SystemStatusLogAccess.add(db=db, sysstslog=SystemStatusLogName.STOP)
    manager.shutdown()
    logger.info(get_filename() + ' manager end')

def start_db_organize(db :Session, cmdstr :str):
    SystemStatusLogAccess.add(db=db, sysstslog=SystemStatusLogName.DB_ORGANIZE)
    if cmdstr == sendcmd.ScrOrder.DB_ORGANIZE_DAYS:
        db_organizer.start_func(db=db, orgcmd=db_organizer.DBOrganizerCmd.ALL)
    elif cmdstr == sendcmd.ScrOrder.DB_ORGANIZE_SYNC:
        db_organizer.start_func(db=db, orgcmd=db_organizer.DBOrganizerCmd.SYNC_PRICELOG)
    elif cmdstr == sendcmd.ScrOrder.DB_ORGANIZE_LOG_2DAYS_CLEANER:
        db_organizer.start_func(db=db, orgcmd=db_organizer.DBOrganizerCmd.PRICELOG_2DAYS_CLEANER)
    elif cmdstr == sendcmd.ScrOrder.DB_ORGANIZE_LOG_CLEANER:
        db_organizer.start_func(db=db, orgcmd=db_organizer.DBOrganizerCmd.PRICELOG_CLEANER)
    return

def scrapingURL(task, db :Session):
    logger = getLogger(cmnlog.LogName.MANAGER)
    match task.cmdstr:
        case sendcmd.ScrOrder.UPDATE:
            logger.info(get_filename() + ' get UPDATE')
            SystemStatusLogAccess.add(db=db, sysstslog=SystemStatusLogName.DATA_UPDATE)
            dlproc.putDlTask(task.url, task.id)
            return
        case sendcmd.ScrOrder.AUTO_UPDATE_ACT_ALL:
            SystemStatusLogAccess.add(db=db, sysstslog=SystemStatusLogName.AUTO_ALL_DATA_UPDATE)
            updateAllItems.updateAllitems(db, dlproc)
            return
        case  sendcmd.ScrOrder.UPDATE_ACT_ALL:
            SystemStatusLogAccess.add(db=db, sysstslog=SystemStatusLogName.ALL_DATA_UPDATE)
            updateAllItems.updateAllitems(db, dlproc)
            return
        case sendcmd.ScrOrder.DB_ORGANIZE_SYNC:
            start_db_organize(db, cmdstr=task.cmdstr)
            return
        case sendcmd.ScrOrder.DB_ORGANIZE_DAYS:
            start_db_organize(db, cmdstr=task.cmdstr)
            return
        case sendcmd.ScrOrder.UPDATE_ONLINE_STORE_POSTAGE:
            SystemStatusLogAccess.add(db=db, sysstslog=SystemStatusLogName.ONLINE_STORE_UPDATE)
            online_store_postage.update_online_store_postage(db=db)
            return

def check_db_organize(db :Session):
    ret = OrganizeLogQuery.get_log(db, name=db_organizer.DBOrganizerCmd.PRICELOG_CLEANER.name)
    if not ret \
        or (ret and not util.isLocalToday(util.utcTolocaltime(ret.created_at))):
        start_db_organize(db, cmdstr=sendcmd.ScrOrder.DB_ORGANIZE_DAYS)
    return

def waitTask(task, result):
    logger = getLogger(cmnlog.LogName.MANAGER)
    logger.info(get_filename() + ' waitTask start')
    psa = getProcStatusAccess()
    with next(get_session()) as db:
        manager_util.writeProcActive(db, psa=psa)
        check_db_organize(db)
        PrefectureDBSetting.init_setting(db=db)
        manager_util.writeProcWaiting(db, psa=psa)
        SystemStatusLogAccess.add(db=db, sysstslog=SystemStatusLogName.ACTIVE)
    while True:
        try:
            t = task.get(timeout=QUEUE_TIMEOUT)
            logger.debug(get_filename() + ' get task')
            if not psa.getStatus() == ProcStatusAccess.ACTIVE:
                with next(get_session()) as db:
                    manager_util.writeProcActive(db, psa=psa)

            if(t.cmdstr == sendcmd.ScrOrder.END):
                logger.info(get_filename() + ' get END')
                break
            elif(t.cmdstr not in sendcmd.ScrOrder.ORDERLIST):
                logger.error(get_filename() + 'not in cmdstr =' + t.cmdstr)
            else:
                with next(get_session()) as db:
                    scrapingURL(t, db=db)
        except queue.Empty:
            with next(get_session()) as db:
                if not psa.getStatus() == ProcStatusAccess.WAITING:
                    manager_util.writeProcWaiting(db, psa=psa)
                update_to_active_for_systemstatuslog(db=db)
            time.sleep(0.1)

def createSubProc():
    global dlproc, parseproc, timerproc
    dlproc = DlProc()
    parseproc = ParseProc()
    timerproc = TimerProc()
    parseproc.setDlProc(dlproc)
    parseproc.start()
    timerproc.start()

def endSubProc():
    global dlproc, parseproc, timerproc
    timerproc.end()
    parseproc.shutdown()
    dlproc.shutdownAll()

def createScrapingManager():
    child_pid = os.fork()
    if child_pid == 0 :
        os.setsid()
        if os.fork():
            sys.exit()
        startQueue()
    else:
        pass



import os
import time
import sys
import queue
from multiprocessing.managers import BaseManager

from typing import Optional

from proc import sendcmd
from proc import updateAllItems

from common import cmnlog, util
from proc.dlmanage import DlProc
from proc.parsemanage import ParseProc
from proc.proc_status import ProcStatusAccess, ProcName
from proc import manager_util

from sqlalchemy.orm import Session
from accessor.read_sqlalchemy import get_session

from common.read_config import (
    get_back_server_config,
    get_back_server_queue_timeout,
)
server_conf = get_back_server_config()
server_addr = server_conf['addr'] #'127.0.0.1'
server_port = int(server_conf['port']) #5000

QUEUE_TIMEOUT = int(get_back_server_queue_timeout()) #5

dlproc :Optional[DlProc] = None
parseproc :Optional[ParseProc] = None

class QueueManager(BaseManager):
    pass

def getProcStatusAccess():
    return ProcStatusAccess(name=ProcName.MANAGER)

def writeAllProcStop(db :Session):
    ProcStatusAccess.delete_all(db)

def writeProcStart(db :Session, psa :Optional[ProcStatusAccess]=None):
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

    # タスクを受け取るキュー
    task_queue = queue.Queue()
    # 結果を通知するキュー
    result_queue = queue.Queue()

    # 2つのキューをAPIとして登録する
    # Windowsの場合はAPI登録にlambdaが使えないので、素直に関数を定義してください
    QueueManager.register('get_task_queue', callable=lambda: task_queue)
    QueueManager.register('get_result_queue', callable=lambda: result_queue)

    # ポート5000を使い、認証暗号を'abc'にする
    # Windowsの場合はアドレスを明記する必要がある（127.0.0.1）
    manager = QueueManager(address=('', server_port), authkey=b'ggacbq')
    # 起動する
    manager.start()
    # ネット経由でキューオブジェクトを取得
    task = manager.get_task_queue()
    result = manager.get_result_queue()

    createSubProc()
    with next(get_session()) as db:
        waitTask(task=task, result=result, db=db)

    # 終了
    endSubProc()
    with next(get_session()) as db:
        writeAllProcStop(db=db)
    manager.shutdown()
    logger.info(get_filename() + ' manager end')

def start_db_organize(db :Session, cmdstr :str):
    from proc import db_organizer
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
    if task.cmdstr == sendcmd.ScrOrder.UPDATE:
        logger.info(get_filename() + ' get UPDATE')
        #dlAndParse(task.url, task.id, logger)
        dlproc.putDlTask(task.url, task.id)
        return
    if task.cmdstr == sendcmd.ScrOrder.UPDATE_ACT_ALL:
        updateAllItems.updateAllitems(db, dlproc)
        return
    if task.cmdstr == sendcmd.ScrOrder.DB_ORGANIZE_SYNC\
        or task.cmdstr == sendcmd.ScrOrder.DB_ORGANIZE_DAYS:
        start_db_organize(db, cmdstr=task.cmdstr)
        return

def check_db_organize(db :Session):
    from accessor.server import OrganizeLogQuery
    from proc import db_organizer
    ret = OrganizeLogQuery.get_log(db, name=db_organizer.DBOrganizerCmd.PRICELOG_CLEANER.name)
    if not ret \
        or (ret and not util.isLocalToday(util.utcTolocaltime(ret.created_at))):
        start_db_organize(db, cmdstr=sendcmd.ScrOrder.DB_ORGANIZE_DAYS)
    return

def waitTask(task, result, db :Session):
    logger = getLogger(cmnlog.LogName.MANAGER)
    logger.info(get_filename() + ' waitTask start')
    psa = getProcStatusAccess()
    manager_util.writeProcActive(db, psa=psa)
    check_db_organize(db)
    manager_util.writeProcWaiting(db, psa=psa)
    while True:
        try:
            t = task.get(timeout=QUEUE_TIMEOUT)
            logger.info(get_filename() + ' get task')
            if not psa.getStatus() == ProcStatusAccess.ACTIVE:
                manager_util.writeProcActive(db, psa=psa)

            if(t.cmdstr == sendcmd.ScrOrder.END):
                logger.info(get_filename() + ' get END')
                break
            elif(t.cmdstr not in sendcmd.ScrOrder.ORDERLIST):
                logger.error(get_filename() + 'not in cmdstr =' + t.cmdstr)
            else:
                scrapingURL(t, db=db)
        except queue.Empty:
            if not psa.getStatus() == ProcStatusAccess.WAITING:
                manager_util.writeProcWaiting(db, psa=psa)
            time.sleep(0.1)

def createSubProc():
    global dlproc, parseproc
    dlproc = DlProc()
    parseproc = ParseProc()
    parseproc.setDlProc(dlproc)
    parseproc.start()

def endSubProc():
    global dlproc, parseproc
    parseproc.shutdown()
    dlproc.shutdownAll()

def createScrapingManager():
    child_pid = os.fork()
    if child_pid == 0 :
        os.setsid()
        #print('child process')
        if os.fork():
            sys.exit()
        startQueue()
        
    else:
        #print('parent process')
        #print('cmd end')
        #sys.exit()
        pass

def sendTask(cmdstr, url='', id=''):
    logger = cmnlog.createLogger(cmnlog.LogName.CLIENT)
    logger.info(get_filename() + ' sendTask start')
    QueueManager.register('get_task_queue')
    QueueManager.register('get_result_queue')

    # サーバーに接続する
    logger.info(get_filename() + ' Connect to server {}...'.format(server_addr))
    # 同じポートと認証暗号を設定する
    m = QueueManager(address=(server_addr, server_port), authkey=b'ggacbq')
    # 接続
    try:
        m.connect()
    except ConnectionRefusedError:
        print("ConnectionRefusedError")
        logger.error(get_filename() + "ConnectionRefusedError")
        return

    # それぞれのキューを取得
    task = m.get_task_queue()
    result = m.get_result_queue()

    cmd = sendcmd.SendCmd(cmdstr, url, id)
    logger.info('{} sendTask {}'.format(get_filename(), cmdstr))

    task.put(cmd)

    logger.info(get_filename() + ' sendTask end')

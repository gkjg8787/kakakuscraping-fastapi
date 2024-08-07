import os
import time
from multiprocessing import Process, Queue
import queue

from common import cmnlog
from proc import (
    getAndWrite,
    manager_util,
    scrapingmanage as scm,
    online_store_postage,
    online_store_copy,
    db_organizer,
)
from proc.proc_status import ProcName
from proc.sendcmd import ScrOrder
from proc.proc_task import (
    DownloadResultTask,
    DirectOrderTask,
)
from accessor.read_sqlalchemy import get_session, Session


def get_filename():
    return os.path.basename(__file__)


class ParseProc:
    def __init__(self):
        self.parse_task_q = Queue()
        self.paproclist: list[ParseInfo] = []

    def getLogger(self):
        logname = cmnlog.LogName.PARSE
        return cmnlog.getLogger(logname)

    def start(self):
        id = 0
        p = self.startParseSchedule(id)
        pinfo = ParseInfo(id, p)
        self.paproclist.append(pinfo)

    def shutdown(self):
        logger = self.getLogger()
        for pi in self.paproclist:
            pi.proc.terminate()
            logger.info(get_filename() + " parseproc terminate id=" + str(pi.id))
        self.paproclist.clear()

    def put_task(self, task):
        self.parse_task_q.put(task)

    def get_task(self, q: Queue, timeout: float):
        try:
            task = q.get(timeout=timeout)
            return task
        except queue.Empty:
            return None

    def runParseProc(self, id):
        logger = self.getLogger()
        logger.info(get_filename() + " start parseproc id=" + str(id))
        with next(get_session()) as db:
            psa = manager_util.writeProcStart(db, pnum=id, name=ProcName.PARSE)
        is_parse = False
        PARSE_QUEUE_TIMEOUT = 5
        autocopysttolc = online_store_copy.AutoCopyOnlineStoreToLocal(logger=logger)

        while True:
            task = self.get_task(q=self.parse_task_q, timeout=PARSE_QUEUE_TIMEOUT)
            if task is None:
                if is_parse:
                    is_parse = False
                    logger.info(
                        get_filename() + " sendTask " + ScrOrder.DB_ORGANIZE_SYNC
                    )
                    scm.sendTask(ScrOrder.DB_ORGANIZE_SYNC, "", "")
                    logger.info(
                        get_filename()
                        + " sendTask "
                        + ScrOrder.DB_ORGANIZE_LOG_2DAYS_CLEANER
                    )
                    scm.sendTask(ScrOrder.DB_ORGANIZE_LOG_2DAYS_CLEANER, "", "")
                else:
                    with next(get_session()) as db:
                        manager_util.writeProcWaiting(db, psa=psa)
                    time.sleep(0.1)
                continue

            if type(task) is DirectOrderTask:
                with next(get_session()) as db:
                    manager_util.writeProcActive(db, psa=psa)
                    self.instruct_update_data(
                        db=db, logger=logger, task=task, autocopysttolc=autocopysttolc
                    )
                continue

            if type(task) is not DownloadResultTask:
                continue
            with next(get_session()) as db:
                manager_util.writeProcActive(db, psa=psa)
                logger.info(
                    get_filename() + " pid=" + str(id) + " start Parse url=" + task.url
                )
                getAndWrite.startParse(
                    db=db,
                    url=task.url,
                    item_id=task.itemid,
                    fname=task.dlhtml,
                    logger=logger,
                )
            is_parse = True
            logger.debug(
                get_filename() + " pid=" + str(id) + " end Parse url=" + task.url
            )

    def startParseSchedule(self, id: int):
        p = Process(target=self.runParseProc, args=(id,))
        p.start()
        return p

    def instruct_update_data(
        self,
        db: Session,
        logger: cmnlog.logging.Logger,
        task: DirectOrderTask,
        autocopysttolc: online_store_copy.AutoCopyOnlineStoreToLocal,
    ):
        match task.cmdstr:
            case ScrOrder.DB_ORGANIZE_SYNC | ScrOrder.DB_ORGANIZE_DAYS:
                logger.info(f"{get_filename()} db organize start")
                self.start_db_organize(db, cmdstr=task.cmdstr)
                logger.info(f"{get_filename()} db organize end")
                return
            case ScrOrder.UPDATE_ONLINE_STORE_POSTAGE:
                logger.info(f"{get_filename()} update online store postage start")
                online_store_postage.update_online_store_postage(db=db)
                logger.info(f"{get_filename()} update online store postage end")
                autocopysttolc.start(db=db)
                return

    def start_db_organize(self, db: Session, cmdstr: str):
        if cmdstr == ScrOrder.DB_ORGANIZE_DAYS:
            db_organizer.start_func(db=db, orgcmd=db_organizer.DBOrganizerCmd.ALL)
        elif cmdstr == ScrOrder.DB_ORGANIZE_SYNC:
            db_organizer.start_func(
                db=db, orgcmd=db_organizer.DBOrganizerCmd.SYNC_PRICELOG
            )
        elif cmdstr == ScrOrder.DB_ORGANIZE_LOG_2DAYS_CLEANER:
            db_organizer.start_func(
                db=db, orgcmd=db_organizer.DBOrganizerCmd.PRICELOG_2DAYS_CLEANER
            )
        elif cmdstr == ScrOrder.DB_ORGANIZE_LOG_CLEANER:
            db_organizer.start_func(
                db=db, orgcmd=db_organizer.DBOrganizerCmd.PRICELOG_CLEANER
            )
        return


class ParseInfo:
    def __init__(self, id: int, proc: Process):
        self.id = id
        self.proc = proc

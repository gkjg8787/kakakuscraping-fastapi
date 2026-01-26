import os
import time
from multiprocessing import Process, Queue
import queue

from common import cmnlog, const_value
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
from proc.proc_task import DownloadResultTask, DirectOrderTask, APIUpdateTask
from accessor.read_sqlalchemy import get_session, Session
from html_parser import api_model


def get_filename():
    return os.path.basename(__file__)


def get_logger():
    return cmnlog.getLogger(cmnlog.LogName.PARSE)


def get_task_from_queue(q: Queue, timeout: float):
    try:
        task = q.get(timeout=timeout)
        return task
    except queue.Empty:
        return None


def create_logger():
    return cmnlog.createLogger(cmnlog.LogName.PARSE)


def run_parse_process(id, taskq):
    logger = create_logger()
    logger.info(get_filename() + " start parseproc id=" + str(id))
    with next(get_session()) as db:
        psa = manager_util.writeProcStart(db, pnum=id, name=ProcName.PARSE)
    is_parse = False
    PARSE_QUEUE_TIMEOUT = 5
    autocopysttolc = online_store_copy.AutoCopyOnlineStoreToLocal(logger=logger)

    try:
        while True:
            task = get_task_from_queue(q=taskq, timeout=PARSE_QUEUE_TIMEOUT)
            if task is None:
                if is_parse:
                    is_parse = False
                    logger.info(
                        get_filename() + " sendTask " + ScrOrder.DB_ORGANIZE_SYNC
                    )
                    scm.sendTask(cmdstr=ScrOrder.DB_ORGANIZE_SYNC)
                    logger.info(
                        get_filename()
                        + " sendTask "
                        + ScrOrder.DB_ORGANIZE_LOG_2DAYS_CLEANER
                    )
                    scm.sendTask(cmdstr=ScrOrder.DB_ORGANIZE_LOG_2DAYS_CLEANER)
                else:
                    with next(get_session()) as db:
                        manager_util.writeProcWaiting(db, psa=psa)
                    time.sleep(0.1)
                continue

            if type(task) is DirectOrderTask:
                with next(get_session()) as db:
                    manager_util.writeProcActive(db, psa=psa)
                    _instruct_update_data(
                        db=db, logger=logger, task=task, autocopysttolc=autocopysttolc
                    )
                continue

            if type(task) is APIUpdateTask:
                with next(get_session()) as db:
                    manager_util.writeProcActive(db, psa=psa)
                    _api_update(pid=id, db=db, task=task, logger=logger)
                    is_parse = True
                    continue
            if not isinstance(task, DownloadResultTask):
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
    except Exception as e:
        logger.error(get_filename() + f" run_parse_process error:{e}")


def _instruct_update_data(
    db: Session,
    logger: cmnlog.logging.Logger,
    task: DirectOrderTask,
    autocopysttolc: online_store_copy.AutoCopyOnlineStoreToLocal,
):
    match task.cmdstr:
        case ScrOrder.DB_ORGANIZE_SYNC | ScrOrder.DB_ORGANIZE_DAYS:
            logger.info(f"{get_filename()} db organize start")
            _start_db_organize(db, cmdstr=task.cmdstr)
            logger.info(f"{get_filename()} db organize end")
            return
        case ScrOrder.UPDATE_ONLINE_STORE_POSTAGE:
            logger.info(f"{get_filename()} update online store postage start")
            online_store_postage.update_online_store_postage(db=db)
            logger.info(f"{get_filename()} update online store postage end")
            autocopysttolc.start(db=db)
            return


def _start_db_organize(db: Session, cmdstr: str):
    if cmdstr == ScrOrder.DB_ORGANIZE_DAYS:
        db_organizer.start_func(db=db, orgcmd=db_organizer.DBOrganizerCmd.ALL)
    elif cmdstr == ScrOrder.DB_ORGANIZE_SYNC:
        db_organizer.start_func(db=db, orgcmd=db_organizer.DBOrganizerCmd.SYNC_PRICELOG)
    elif cmdstr == ScrOrder.DB_ORGANIZE_LOG_2DAYS_CLEANER:
        db_organizer.start_func(
            db=db, orgcmd=db_organizer.DBOrganizerCmd.PRICELOG_2DAYS_CLEANER
        )
    elif cmdstr == ScrOrder.DB_ORGANIZE_LOG_CLEANER:
        db_organizer.start_func(
            db=db, orgcmd=db_organizer.DBOrganizerCmd.PRICELOG_CLEANER
        )
    return


def _api_update(
    pid: int,
    db: Session,
    task: APIUpdateTask,
    logger: cmnlog.logging.Logger,
):
    parseitems_dict: dict[int, api_model.ParseItemsForPriceUpdate] = task.data
    if parseitems_dict is None:
        logger.warning(get_filename() + " api update , data is None")
        return
    if type(parseitems_dict) is not dict:
        logger.warning(
            get_filename()
            + " api update , data type is not dict type="
            + type(parseitems_dict)
        )
        return
    for url_id, parseitems in parseitems_dict.items():
        if type(parseitems) is not api_model.ParseItemsForPriceUpdate:
            logger.warning(
                f"{get_filename()} api update , data type is not {api_model.ParseItemsForPriceUpdate.__class__.__name__} type={type(parseitems)}"
            )
            continue
        logger.info(
            get_filename()
            + " pid="
            + str(pid)
            + " start api update url="
            + parseitems.get_url()
        )
        getAndWrite._start_parse(
            parseitems=parseitems,
            db=db,
            url=parseitems.get_url(),
            item_id=const_value.NONE_ID,
            url_id=url_id,
            logger=logger,
        )


class ParseProc:
    def __init__(self):
        self.parse_task_q = Queue()
        self.paproclist: list[ParseInfo] = []

    def start(self):
        id = 0
        p = self.startParseSchedule(id)
        pinfo = ParseInfo(id, p)
        self.paproclist.append(pinfo)

    def shutdown(self):
        logger = get_logger()
        for pi in self.paproclist:
            pi.proc.terminate()
            logger.info(get_filename() + " parseproc terminate id=" + str(pi.id))
        self.paproclist.clear()

    def put_task(self, task):
        try:
            self.parse_task_q.put(task)
        except Exception as e:
            logger = get_logger()
            logger.error(get_filename() + f" put_task error:{e}")

    def startParseSchedule(self, id: int):
        try:
            p = Process(target=run_parse_process, args=(id, self.parse_task_q))
            p.start()
            return p
        except Exception as e:
            logger = get_logger()
            logger.error(get_filename() + f" startParseSchedule error:{e}")
            raise e


class ParseInfo:
    def __init__(self, id: int, proc: Process):
        self.id = id
        self.proc = proc

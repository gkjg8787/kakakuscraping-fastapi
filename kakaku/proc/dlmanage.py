import os
from multiprocessing import Process, Queue
import queue
import time
from urllib.parse import urlparse

from downloader import download_html
from common import cmnlog
from common.read_config import get_back_server_queue_timeout, get_support_url
from accessor.read_sqlalchemy import get_session
from proc import manager_util
from proc.proc_status import ProcName
from proc.proc_task import DownloadResultTask

QUEUE_TIMEOUT = float(get_back_server_queue_timeout())  # 5


def get_filename():
    return os.path.basename(__file__)


class DlProc:
    def __init__(self, retq: Queue):
        self.dlproclist: dict[str, DlInfo] = dict()
        self.taskretq = retq

    def getLogger(self, pid=-1):
        logname = cmnlog.LogName.DOWNLOAD
        if pid > -1:
            logname += "{:0=2}".format(pid)
        return cmnlog.getLogger(logname)

    def removeLogger(self, pid=-1):
        logname = cmnlog.LogName.DOWNLOAD
        if pid > -1:
            logname += "{:0=2}".format(pid)
        cmnlog.removeLogger(logname)

    def createLogger(self, pid=-1):
        logname = cmnlog.LogName.DOWNLOAD
        if pid > -1:
            logname += "{:0=2}".format(pid)
        return cmnlog.createLogger(logname)

    def getParseTask(self):
        logger = self.getLogger()
        if self.taskretq is None:
            return None
        try:
            task = self.taskretq.get(timeout=QUEUE_TIMEOUT)
            logger.info(get_filename() + " get download ret")
            return task
        except queue.Empty:
            return None

    def runDlproc(self, id: int, taskq, retq):
        logger = self.createLogger(id)
        stime = 0
        etime = 0
        logger.info(get_filename() + " start dlproc id=" + str(id))
        db = next(get_session())
        psa = manager_util.writeProcStart(db, pnum=id, name=ProcName.DOWNLOAD)
        manager_util.writeProcWaiting(db, psa=psa)
        while True:
            try:
                task: DownloadResultTask = taskq.get(timeout=QUEUE_TIMEOUT)
                etime = time.time()
                if etime - stime < 1:
                    time.sleep((1 - (etime - stime)))
                logger.debug(get_filename() + " get dltask url=" + task.url)
                manager_util.writeProcActive(db, psa=psa)
                dlhtml = download_html.downLoadHtml(task.url)
                stime = time.time()
                if len(dlhtml) == 0:
                    logger.error(get_filename() + " fail download url=" + task.url)
                    manager_util.writeProcFault(db, psa=psa)
                    continue
                logger.debug(get_filename() + " download html=" + dlhtml)
                task.dlhtml = dlhtml
                retq.put(task)
                logger.info(get_filename() + " put parsetask html=" + dlhtml)
            except queue.Empty:
                manager_util.writeProcWaiting(db, psa=psa)
                time.sleep(0.1)

    def putDlTask(self, url, itemid):
        logger = self.getLogger()
        parsed_url = urlparse(url)
        logger.info(get_filename() + " put host=" + parsed_url.netloc)
        support_urls = get_support_url()
        if parsed_url.netloc not in list(support_urls.values()):
            logger.warning(get_filename() + " not supported url=" + parsed_url.netloc)
            return
        if len(self.dlproclist) == 0:
            self.createDlProc(0, parsed_url)
            logger.info(get_filename() + " create proc id=0 host=" + parsed_url.netloc)
        if parsed_url.netloc not in self.dlproclist:
            self.createDlProc(len(self.dlproclist), parsed_url)
            logger.info(
                get_filename()
                + " create proc id="
                + str(self.dlproclist[parsed_url.netloc].id)
                + " host="
                + parsed_url.netloc
            )

        task = DownloadResultTask(url=url, itemid=itemid)
        self.dlproclist[parsed_url.netloc].taskq.put(task)
        self.dlproclist[parsed_url.netloc].updatePutTime()
        logger.debug(get_filename() + " put task")

    def createDlProc(self, id: int, parsed_url):
        p, taskq = self.startDlSchedule(id, self.taskretq)
        info = DlInfo(id, p, parsed_url.netloc, taskq)
        self.dlproclist[parsed_url.netloc] = info

    def startDlSchedule(self, id: int, retq):
        taskq = Queue()
        p = Process(target=self.runDlproc, args=(id, taskq, retq))
        p.start()
        return p, taskq

    def shutdownAll(self):
        logger = self.getLogger()
        logger.info(get_filename() + " shutdown all proc")
        if len(self.dlproclist) > 0:
            for v in self.dlproclist.values():
                v.proc.terminate()
                logger.info(
                    get_filename()
                    + " dlproc terminate id="
                    + str(v.id)
                    + " host="
                    + v.hostname
                )
                self.removeLogger(v.id)
            self.dlproclist.clear()


class DlInfo:
    def __init__(self, id: int, proc: Process, hostname: str, taskq: Queue):
        self.id = id
        self.proc = proc
        self.hostname = hostname
        self.taskq = taskq
        self.starttime = time.time()
        self.updateputtime = self.starttime

    def updatePutTime(self):
        self.updateputtime = time.time()

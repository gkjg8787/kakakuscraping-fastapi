import os
import time
from multiprocessing import Process


from common import cmnlog
from proc import getAndWrite

from proc import db_organizer

from proc.proc_status import ProcName
from proc import manager_util

from accessor.read_sqlalchemy import get_session


def get_filename():
    return os.path.basename(__file__)

class ParseProc:
    def __init__(self):
        self.dlproc = None
        self.paproclist = []

    def getLogger(self):
        logname = cmnlog.LogName.PARSE
        return cmnlog.getLogger(logname)

    def setDlProc(self, dlproc):
        self.dlproc = dlproc

    def start(self):
        id = 0
        p = self.startParseSchedule(id)
        pinfo = ParseInfo(id, p)
        self.paproclist.append(pinfo)

    def shutdown(self):
        logger = self.getLogger()
        for pi in self.paproclist:
            pi.proc.terminate()
            logger.info(get_filename() + 'parseproc terminate id=' + str(pi.id))
        self.paproclist.clear()

    def runParseProc(self, id):
        logger = self.getLogger()
        logger.info(get_filename() + ' start parseproc id=' + str(id))
        db = next(get_session())
        psa = manager_util.writeProcStart(db, pnum=id, name=ProcName.PARSE)
        if (self.dlproc == None):
            logger.error(get_filename() + ' dlproc None')
            manager_util.writeProcFault(db, psa=psa)
            return
        is_parse = False
        while True:
            task = self.dlproc.getParseTask()
            if (task == None):
                manager_util.writeProcWaiting(db, psa=psa)
                if is_parse:
                    is_parse = False
                    logger.info(get_filename() + " start db_organizer sync")
                    db_organizer.start_func(db, orgcmd=db_organizer.DBOrganizerCmd.SYNC_PRICELOG)
                    logger.info(get_filename() + " end db_organizer sync")
                else:
                    time.sleep(0.1)
                continue
            manager_util.writeProcActive(db, psa=psa)
            logger.info(get_filename() + ' pid=' + str(id) + ' start Parse url='+ task.url)
            getAndWrite.startParse(db=db, url=task.url, item_id=task.itemid, fname=task.dlhtml, logger=logger)
            is_parse = True
            logger.info(get_filename() + ' pid=' + str(id) + ' end Parse url='+ task.url)

    def startParseSchedule(self, id):
        p = Process(target=self.runParseProc,args=(id,))
        p.start()
        return p

class ParseInfo:
    def __init__(self, id, proc):
        self.id = id
        self.proc = proc


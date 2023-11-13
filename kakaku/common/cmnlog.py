
import logging
import os
from common.read_config import get_log_dir

LOGGING_LEVEL = logging.DEBUG
# initLogger使用後の呼び出し
def getLogger(fn):
    return logging.getLogger(fn)

# initLoggerなしでの呼び出し1回目
def createLogger(fn):
    logdir = get_log_dir()
    return _setLogger(logdir, fn)

def removeLogger(fn):
    logdir = get_log_dir()
    logger = logging.getLogger(fn)
    logpath = os.path.join(logdir ,fn + '.log')
    flh = logging.FileHandler(logpath)
    logger.removeHandler(flh)

def deleteLogger(fn):
    logger = logging.getLogger(fn)
    del logging.Logger.manager.loggerDict[logger.name]

def _setLogger(dir, fn):
    logpath = os.path.join(dir ,fn + '.log')
    logger = logging.getLogger(fn)
    flh = logging.FileHandler(logpath)
    form = logging.Formatter(fmt='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    flh.setFormatter(form)
    logger.setLevel(LOGGING_LEVEL)
    logger.addHandler(flh)
    return logger

def initProcessLogger():
    createLogger(LogName.MANAGER)
    createLogger(LogName.DOWNLOAD)
    createLogger(LogName.PARSE)
    createLogger(LogName.DB_ORGANIZE)

class LogName:
    MANAGER = "scrapingmanage"
    CLIENT = "client"
    DOWNLOAD = "dlproc"
    PARSE ="htmlparse"
    SEARCH = "search"
    DB_ORGANIZE = "db_organize"
    ITEMCOMB = "itemcomb"

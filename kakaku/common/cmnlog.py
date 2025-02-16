import logging
import os
from common.read_config import get_log_dir

LOGGING_LEVEL = logging.INFO


# initLogger使用後の呼び出し
def getLogger(fn):
    return logging.getLogger(fn)


def getLogPath(fn):
    return os.path.join(get_log_dir(), fn + ".log")


# initLoggerなしでの呼び出し1回目
def createLogger(fn):
    return _setLogger(fn)


def removeLogger(fn):
    logger = logging.getLogger(fn)
    logpath = getLogPath(fn)
    flh = logging.FileHandler(logpath)
    logger.removeHandler(flh)


def deleteLogger(fn):
    logger = logging.getLogger(fn)
    del logging.Logger.manager.loggerDict[logger.name]


def _setLogger(fn):
    logpath = getLogPath(fn)
    logger = logging.getLogger(fn)
    flh = logging.FileHandler(logpath)
    form = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    flh.setFormatter(form)
    logger.setLevel(LOGGING_LEVEL)
    logger.addHandler(flh)
    return logger


def initProcessLogger():
    createLogger(LogName.MANAGER)
    createLogger(LogName.DOWNLOAD)
    createLogger(LogName.PARSE)
    createLogger(LogName.DB_ORGANIZE)


def initRooterLogger():
    createLogger(LogName.SEARCH)
    createLogger(LogName.ITEMCOMB)
    createLogger(LogName.MACHINELEARN)


class LogName:
    MANAGER = "scrapingmanage"
    CLIENT = "client"
    DOWNLOAD = "dlproc"
    PARSE = "htmlparse"
    SEARCH = "search"
    DB_ORGANIZE = "db_organize"
    ITEMCOMB = "itemcomb"
    TIMER = "timer"
    MACHINELEARN = "ml"

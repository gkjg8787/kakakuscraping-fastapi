import os

from common import cmnlog

from .queuemanager import (
    QueueManager,
    server_addr,
    server_port,
    server_pswd,
)

from proc import sendcmd


def get_filename():
    return os.path.basename(__file__)


def sendTask(cmdstr: str, url="", id=""):
    cmnlog.deleteLogger(cmnlog.LogName.CLIENT)
    logger = cmnlog.createLogger(cmnlog.LogName.CLIENT)
    logger.debug(get_filename() + " sendTask start")
    QueueManager.register("get_task_queue")
    QueueManager.register("get_result_queue")

    logger.debug(get_filename() + " Connect to server {}...".format(server_addr))
    m = QueueManager(address=(server_addr, server_port), authkey=server_pswd)
    try:
        m.connect()
    except ConnectionRefusedError:
        print("ConnectionRefusedError")
        logger.error(get_filename() + "ConnectionRefusedError")
        return

    task = m.get_task_queue()
    # result = m.get_result_queue()

    cmd = sendcmd.SendCmd(cmdstr, url, id)
    logger.info("{} sendTask {}".format(get_filename(), cmdstr))

    task.put(cmd)

    logger.debug(get_filename() + " sendTask end")

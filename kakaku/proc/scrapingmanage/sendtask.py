import os
from typing import Any

from common import cmnlog, const_value

from .queuemanager import (
    QueueManager,
    server_addr,
    server_port,
    server_pswd,
)

from proc import sendcmd


def get_filename():
    return os.path.basename(__file__)


def sendTask(
    cmdstr: str, url: str = "", id: int = const_value.NONE_ID, data: Any = None
):
    cmnlog.deleteLogger(cmnlog.LogName.CLIENT)
    logger = cmnlog.createLogger(cmnlog.LogName.CLIENT)
    logger.debug(get_filename() + " sendTask start")

    logger.debug(get_filename() + " Connect to server {}...".format(server_addr))
    m = QueueManager(address=(server_addr, server_port), authkey=server_pswd)
    try:
        m.connect()
    except ConnectionRefusedError:
        print("ConnectionRefusedError")
        logger.error(get_filename() + " ConnectionRefusedError")
        return

    task = m.get_task_queue()
    # result = m.get_result_queue()

    cmd = sendcmd.SendCmd(cmdstr=cmdstr, url=url, id=id, data=data)
    logger.info("{} sendTask {}".format(get_filename(), cmdstr))

    task.put(cmd)

    logger.debug(get_filename() + " sendTask end")

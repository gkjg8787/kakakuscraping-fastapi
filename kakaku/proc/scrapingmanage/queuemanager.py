from multiprocessing.managers import BaseManager


from common.read_config import (
    get_back_server_config,
)


server_conf = get_back_server_config()
server_addr = server_conf["addr"]  # '127.0.0.1'
server_port = int(server_conf["port"])  # 5000
server_pswd = b"ggacbq"


class QueueManager(BaseManager):
    pass

class DownloadResultTask:
    dlhtml = ""

    def __init__(self, url: str, itemid: int):
        self.url = url
        self.itemid = itemid


class DirectOrderTask:
    cmdstr: str

    def __init__(self, cmdstr: str):
        self.cmdstr = cmdstr

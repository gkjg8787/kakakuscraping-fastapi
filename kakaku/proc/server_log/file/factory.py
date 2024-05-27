import re
from datetime import datetime

from ..model import ServerLogFile, ServerLogLine


class ServerLogLineParse:

    def toServerLogLine(self, text: str) -> ServerLogLine:
        if not text:
            return ServerLogLine(text="")
        ptn = r"(.+) - (.+) - (.+) - (.+)"
        m = re.findall(ptn, text)
        datefmt = "%Y-%m-%d %H:%M:%S.%f"
        d = datetime.strptime(m[0][0], datefmt)
        f = re.match(r"(.+\.py),? (.+)", m[0][3])
        if not f:
            return ServerLogLine(
                rawtext=text,
                created_at=d,
                filename="",
                loglevel=m[0][2],
                text=m[0][3],
            )
        return ServerLogLine(
            rawtext=text,
            created_at=d,
            filename=f[1],
            loglevel=m[0][2],
            text=f[2],
        )


class ServerLogLineFactory:
    @classmethod
    def create(cls, rawtext: str):
        return ServerLogLineParse().toServerLogLine(text=rawtext)


class ServerLogFileFactory:
    @classmethod
    def create(cls, rawtext: str, filename: str):
        slll: list[ServerLogLine] = []
        for l in rawtext.split("\n"):
            if not l:
                continue
            slll.append(ServerLogLineFactory.create(rawtext=l))
        return ServerLogFile(logs=slll, filename=filename)

    @classmethod
    def create_by_list(cls, textlist: list[str], filename: str):
        slll: list[ServerLogLine] = []
        for l in textlist:
            if not l:
                continue
            slll.append(ServerLogLineFactory.create(rawtext=l))
        return ServerLogFile(logs=slll, filename=filename)

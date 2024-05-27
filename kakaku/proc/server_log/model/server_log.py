from datetime import datetime

from pydantic import BaseModel


class ServerLogLine(BaseModel):
    created_at: datetime | None
    loglevel: str = ""
    filename: str = ""
    classname: str = ""
    funcname: str = ""
    text: str = ""
    rawtext: str


class ServerLogFile(BaseModel):
    logs: list[ServerLogLine]
    filename: str

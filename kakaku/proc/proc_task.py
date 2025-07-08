from pydantic import BaseModel
from typing import Any


class DownloadResultTask(BaseModel):
    url: str
    itemid: int
    dlhtml: str = ""


class DirectOrderTask(BaseModel):
    cmdstr: str


class APIUpdateTask(DirectOrderTask):
    data: Any

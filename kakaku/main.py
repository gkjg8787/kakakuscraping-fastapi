from contextlib import asynccontextmanager

from fastapi import FastAPI, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from routers import (
    users,
    search,
    calcitemcomb,
    admin,
)
from parameter_parser.admin import ProcCtrlForm
from template_value.admin import BackServerCtrl
from common.filter_name import SystemCtrlBtnName
from common.read_config import get_auto_startup_backserver


@asynccontextmanager
async def lifespan(app: FastAPI):
    if is_auto_start_backserver():
        ctrlbackserver(cmd=SystemCtrlBtnName.STARTUP)
    yield
    if is_auto_start_backserver():
        ctrlbackserver(cmd=SystemCtrlBtnName.STOP)


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(users.router)
app.include_router(search.router)
app.include_router(calcitemcomb.router)
app.include_router(admin.router)


def ctrlbackserver(cmd: SystemCtrlBtnName):
    pcf = ProcCtrlForm(system_ctrl_btn=cmd.value)
    bsc = BackServerCtrl(pcf)
    bsc.action()


def is_auto_start_backserver():
    conf = get_auto_startup_backserver()
    for k in conf.keys():
        if k.lower() == "auto" and conf[k]:
            return True
    return False


@app.get("/")
async def root(request: Request):
    return RedirectResponse(
        url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
    )

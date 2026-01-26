from contextlib import asynccontextmanager

from fastapi import FastAPI, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from routers import (
    users,
    search,
    calcitemcomb,
    admin,
    api,
)
from parameter_parser.admin import ProcCtrlForm
from template_value.admin import BackServerCtrl
from common.filter_name import SystemCtrlBtnName
from common.read_config import get_auto_startup_backserver, get_api_options
from common.cmnlog import initRooterLogger


@asynccontextmanager
async def lifespan(app: FastAPI):
    initRooterLogger()
    if is_auto_start_backserver():
        await ctrlbackserver(cmd=SystemCtrlBtnName.STARTUP)
    yield
    if is_auto_start_backserver():
        await ctrlbackserver(cmd=SystemCtrlBtnName.STOP)


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(users.router)
app.include_router(search.router)
app.include_router(calcitemcomb.router)
app.include_router(admin.router)
if get_api_options().enable:
    app.include_router(api.router)


async def ctrlbackserver(cmd: SystemCtrlBtnName):
    pcf = ProcCtrlForm(system_ctrl_btn=cmd.value)
    bsc = BackServerCtrl(pcf)
    await bsc.async_action()


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

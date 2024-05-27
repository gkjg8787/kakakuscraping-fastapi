from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse

from sqlalchemy.orm import Session

from accessor.read_sqlalchemy import get_session

from common import read_templates

from template_value.admin import (
    DashBoardTemplate,
    BackServerCtrl,
    ServerLogDisplay,
    TempDirDisplay,
)
from parameter_parser.admin import ProcCtrlForm, LogFilterQuery


router = APIRouter(prefix="/admin", tags=["admin"])

templates = read_templates.templates


@router.get("/dashboard/", response_class=HTMLResponse)
def read_admin_dashboard(request: Request, db: Session = Depends(get_session)):
    dbt = DashBoardTemplate(db=db)
    return templates.TemplateResponse(
        request=request, name="admin/controlpanel.html", context=dbt.get_context()
    )


@router.post("/dashboard/svchg/")
def read_admin_dashboard_svchg(
    request: Request, background_tasks: BackgroundTasks, pcf: ProcCtrlForm = Depends()
):
    bsc = BackServerCtrl(pcf)
    background_tasks.add_task(bsc.action)
    context = {"errmsg": ""}
    return templates.TemplateResponse(
        request=request, name="admin/svchg.html", context=context
    )


@router.get("/dashboard/log", response_class=HTMLResponse)
def read_admin_server_log(request: Request, lfq: LogFilterQuery = Depends()):
    sld = ServerLogDisplay(lfq=lfq)
    return templates.TemplateResponse(
        request=request, name="admin/serverlogdisplay.html", context=sld.get_context()
    )


@router.get("/dashboard/temp", response_class=HTMLResponse)
def read_admin_server_temp_file(request: Request):
    tdd = TempDirDisplay()
    return templates.TemplateResponse(
        request=request, name="admin/tempdirdisplay.html", context=tdd.get_context()
    )

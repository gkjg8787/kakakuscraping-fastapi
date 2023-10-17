from fastapi import APIRouter, Request, status, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse

from sqlalchemy.orm import Session

from accessor.read_sqlalchemy import get_session

from common import read_templates

from template_value.admin import DashBoardTemplate, BackServerCtrl
from parameter_parser.admin import ProcCtrlForm




router = APIRouter(
    prefix="/admin"
    ,tags=["admin"]
)

templates = read_templates.templates

@router.get("/dashboard/", response_class=HTMLResponse)
def read_admin_dashboard(request: Request, db :Session = Depends(get_session)):
    dbt = DashBoardTemplate(request, db=db)
    return templates.TemplateResponse(
        "admin/controlpanel.html"
        ,dict(dbt)
        )

@router.post("/dashboard/svchg/")
def read_admin_dashboard_svchg(request: Request, background_tasks: BackgroundTasks, pcf :ProcCtrlForm = Depends()):
    bsc = BackServerCtrl(pcf)
    background_tasks.add_task(bsc.action)
    context = {
        "request":request,
        "errmsg":""
        }
    return templates.TemplateResponse(
        "admin/svchg.html"
        ,context
    )

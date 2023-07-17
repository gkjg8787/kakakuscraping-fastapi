from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import RedirectResponse, HTMLResponse

from common import read_templates

from template_value.admin import DashBoardTemplate, SystemCtrlBtnName
from parameter_parser.admin import ProcCtrlForm

from pathlib import Path
import subprocess


router = APIRouter(
    prefix="/admin"
    ,tags=["admin"]
)

templates = read_templates.templates

@router.get("/dashboard/", response_class=HTMLResponse)
def read_admin_dashboard(request: Request):
    dbt = DashBoardTemplate(request)
    return templates.TemplateResponse(
        "admin/controlpanel.html"
        ,dict(dbt)
        )

@router.post("/dashboard/post/")
def read_admin_dashboard_post(request: Request, pcf :ProcCtrlForm = Depends()):
    """ server change action """
    proc_act(pcf.proc_action)
    return RedirectResponse(url=request.url_for("read_admin_dashboard")
                            ,status_code=status.HTTP_302_FOUND)

def proc_act(action):
    base_path = Path(__file__).resolve().parent.parent
    cmd = ["python3", str(Path(base_path, "proc_manage.py"))]
    if action == SystemCtrlBtnName.STARTUP.value:
        cmd.append("start")
    if action == SystemCtrlBtnName.STOP.value:
        cmd.append("end")
    if action == SystemCtrlBtnName.RESTART.value:
        cmd.append("restart")
    subprocess.run(cmd)
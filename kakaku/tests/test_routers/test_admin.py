import time

from fastapi.testclient import TestClient

from main import app
from proc import system_status as syssts
from proc import get_sys_status
from accessor.read_sqlalchemy import get_session
from common import filter_name
from tests.test_db import test_db, drop_test_db
from tests.test_routers.test_common import (
    RedirectCheckValue,
    check_redirect,
    is_html,
)

client = TestClient(app)
prefix = '/admin'

def check_status_waittime(jstsname :str, waittime :int = 0):
    #db = next(get_session())
    #sysstr = get_sys_status.getSystemStatus(db)
    #if syssts.SystemStatusToJName.get_jname(sysstr) != jstsname:
    time.sleep(waittime)
    response = client.get(
        f'{prefix}/dashboard/',
    )
    assert response.status_code == 200
    is_html(response.text)
    assert '管理画面' in response.text
    assert f'ステータス：{jstsname}' in response.text

def test_read_admin_dashboard_stop():
    check_status_waittime(
        syssts.SystemStatusToJName.get_jname(syssts.SystemStatus.STOP.name)
        )

def test_read_admin_dashboard_svchg_no_data():
    response = client.post(
        f'{prefix}/dashboard/svchg/',
    )
    assert response.status_code == 422

def post_startup_check():
    response = client.post(
        f'{prefix}/dashboard/svchg/',
        data={filter_name.DashBoardPostName.SYSTEM_CTRL_BTN.value:filter_name.SystemCtrlBtnName.STARTUP.value},
    )
    #check_redirect(response, [ RedirectCheckValue(status_code=302, location=f'{prefix}/dashboard/') ])
    assert response.status_code == 200
    assert 'サーバ状態の更新' in response.text
    check_status_waittime(
        syssts.SystemStatusToJName.get_jname(syssts.SystemStatus.ACTIVE.name),
        waittime=3
        )

def test_read_admin_dashboard_svchg_startup_and_stop():
    post_startup_check()

    response = client.post(
        f'{prefix}/dashboard/svchg/',
        data={filter_name.DashBoardPostName.SYSTEM_CTRL_BTN.value:filter_name.SystemCtrlBtnName.STOP.value},
    )
    #check_redirect(response, [ RedirectCheckValue(status_code=302, location=f'{prefix}/dashboard/') ])
    assert response.status_code == 200
    assert 'サーバ状態の更新' in response.text
    check_status_waittime(
        syssts.SystemStatusToJName.get_jname(syssts.SystemStatus.STOP.name),
        waittime=3
        )

def test_read_admin_dashboard_svchg_startup_and_restart():
    post_startup_check()

    response = client.post(
        f'{prefix}/dashboard/svchg/',
        data={filter_name.DashBoardPostName.SYSTEM_CTRL_BTN.value:filter_name.SystemCtrlBtnName.RESTART.value},
    )
    #check_redirect(response, [ RedirectCheckValue(status_code=302, location=f'{prefix}/dashboard/') ])
    assert response.status_code == 200
    assert 'サーバ状態の更新' in response.text
    check_status_waittime(
        syssts.SystemStatusToJName.get_jname(syssts.SystemStatus.ACTIVE.name),
        waittime=4
        )

    response = client.post(
        f'{prefix}/dashboard/svchg/',
        data={filter_name.DashBoardPostName.SYSTEM_CTRL_BTN.value:filter_name.SystemCtrlBtnName.STOP.value},
    )




import time

from fastapi.testclient import TestClient

from main import app
from proc import system_status as syssts
from proc import get_sys_status
from accessor.read_sqlalchemy import Session, get_session, is_postgre
from accessor.item.item import NewestQuery
from common import filter_name
from tests.test_routers.test_common import (
    is_html,
)


client = TestClient(app)
prefix = "/admin"


def is_testable_db(db: Session | None = None):
    if is_postgre():
        return False
    if not db:
        return False
    results = NewestQuery.get_raw_newest_data_all(db)
    if results:
        return False
    return True


def check_status_waittime(db: Session, jstsname: str, waittime: int = 0):
    sumtime = 0
    while waittime > 0:
        sysstr = get_sys_status.getSystemStatus(db)
        if syssts.SystemStatusToJName.get_jname(sysstr) == jstsname:
            break
        assert sumtime < waittime
        sumtime += 1
        time.sleep(1)
    time.sleep(1)
    response = client.get(
        f"{prefix}/dashboard/",
    )
    assert response.status_code == 200
    is_html(response.text)
    assert "管理画面" in response.text
    assert f"ステータス：{jstsname}" in response.text


def test_read_admin_dashboard_stop():
    test_db = next(get_session())
    check_status_waittime(
        db=test_db,
        jstsname=syssts.SystemStatusToJName.get_jname(syssts.SystemStatus.STOP.name),
    )


def test_read_admin_dashboard_svchg_no_data():
    response = client.post(
        f"{prefix}/dashboard/svchg/",
    )
    assert response.status_code == 422


def post_startup_check(db: Session):
    response = client.post(
        f"{prefix}/dashboard/svchg/",
        data={
            filter_name.DashBoardPostName.SYSTEM_CTRL_BTN.value: filter_name.SystemCtrlBtnName.STARTUP.value
        },
    )
    # check_redirect(response, [ RedirectCheckValue(status_code=302, location=f'{prefix}/dashboard/') ])
    assert response.status_code == 200
    assert "サーバ状態の更新" in response.text
    check_status_waittime(
        db=db,
        jstsname=syssts.SystemStatusToJName.get_jname(syssts.SystemStatus.ACTIVE.name),
        waittime=9,
    )


def test_read_admin_dashboard_svchg_startup_and_stop():
    test_db = next(get_session())
    if not is_testable_db(test_db):
        return
    post_startup_check(test_db)

    response = client.post(
        f"{prefix}/dashboard/svchg/",
        data={
            filter_name.DashBoardPostName.SYSTEM_CTRL_BTN.value: filter_name.SystemCtrlBtnName.STOP.value
        },
    )
    # check_redirect(response, [ RedirectCheckValue(status_code=302, location=f'{prefix}/dashboard/') ])
    assert response.status_code == 200
    assert "サーバ状態の更新" in response.text
    check_status_waittime(
        db=test_db,
        jstsname=syssts.SystemStatusToJName.get_jname(syssts.SystemStatus.STOP.name),
        waittime=7,
    )


def test_read_admin_dashboard_svchg_startup_and_restart():
    test_db = next(get_session())
    if not is_testable_db(test_db):
        return
    post_startup_check(test_db)

    response = client.post(
        f"{prefix}/dashboard/svchg/",
        data={
            filter_name.DashBoardPostName.SYSTEM_CTRL_BTN.value: filter_name.SystemCtrlBtnName.RESTART.value
        },
    )
    # check_redirect(response, [ RedirectCheckValue(status_code=302, location=f'{prefix}/dashboard/') ])
    assert response.status_code == 200
    assert "サーバ状態の更新" in response.text
    check_status_waittime(
        db=test_db,
        jstsname=syssts.SystemStatusToJName.get_jname(syssts.SystemStatus.ACTIVE.name),
        waittime=12,
    )

    response = client.post(
        f"{prefix}/dashboard/svchg/",
        data={
            filter_name.DashBoardPostName.SYSTEM_CTRL_BTN.value: filter_name.SystemCtrlBtnName.STOP.value
        },
    )

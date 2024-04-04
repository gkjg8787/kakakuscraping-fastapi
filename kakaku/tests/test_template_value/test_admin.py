from datetime import datetime
from common import read_config, filter_name
from template_value import admin
from proc.auto_update import AutoUpdateStatus


def test_DashBoardTemplate_is_update_for_today_complete_no_list():
    up_str_list: list[str] = []
    ret = admin.DashBoardTemplate.is_update_for_today_complete(up_str_list)
    assert ret == False


def test_DashBoardTemplate_is_update_for_today_complete_ng_single(mocker):
    up_str_list: list[str] = ["10:10"]
    return_date: datetime = datetime.strptime("2024/01/10 10:00", "%Y/%m/%d %H:%M")
    m = mocker.patch("template_value.admin.utcTolocaltime", return_value=return_date)
    ret = admin.DashBoardTemplate.is_update_for_today_complete(up_str_list)
    assert ret == False


def test_DashBoardTemplate_is_update_for_today_complete_ng_multi(mocker):
    up_str_list: list[str] = ["10:10", "14:30"]
    return_date: datetime = datetime.strptime("2024/01/10 12:40", "%Y/%m/%d %H:%M")
    m = mocker.patch("template_value.admin.utcTolocaltime", return_value=return_date)
    ret = admin.DashBoardTemplate.is_update_for_today_complete(up_str_list)
    assert ret == False


def test_DashBoardTemplate_is_update_for_today_complete_ok_single(mocker):
    up_str_list: list[str] = ["20:00"]
    return_date: datetime = datetime.strptime("2024/01/10 20:01", "%Y/%m/%d %H:%M")
    m = mocker.patch("template_value.admin.utcTolocaltime", return_value=return_date)
    ret = admin.DashBoardTemplate.is_update_for_today_complete(up_str_list)
    assert ret == True


def test_DashBoardTemplate_is_update_for_today_complete_ok_multi(mocker):
    up_str_list: list[str] = ["01:00", "06:00", "12:00", "18:00"]
    return_date: datetime = datetime.strptime("2024/01/10 20:01", "%Y/%m/%d %H:%M")
    m = mocker.patch("template_value.admin.utcTolocaltime", return_value=return_date)
    ret = admin.DashBoardTemplate.is_update_for_today_complete(up_str_list)
    assert ret == True


def test_DashBoardTemplate_create_online_store_autoupdate_schedule_no_list(mocker):
    return_list: list[str] = []
    m = mocker.patch(
        "common.read_config.get_auto_update_online_store_time", return_value=return_list
    )
    ret_list = admin.DashBoardTemplate.create_online_store_autoupdate_schedule()
    assert len(ret_list) == 0


def test_DashBoardTemplate_create_online_store_autoupdate_schedule_ng_single(mocker):
    return_list: list[str] = ["25:00"]
    m = mocker.patch(
        "common.read_config.get_auto_update_online_store_time", return_value=return_list
    )
    ret_list = admin.DashBoardTemplate.create_online_store_autoupdate_schedule()
    assert len(ret_list) == 0


def test_DashBoardTemplate_create_online_store_autoupdate_schedule_ok_single_1(mocker):
    return_list: list[str] = ["10:10"]
    m = mocker.patch(
        "common.read_config.get_auto_update_online_store_time", return_value=return_list
    )
    ret_list = admin.DashBoardTemplate.create_online_store_autoupdate_schedule()
    assert len(ret_list) == 1
    assert return_list[0] == ret_list[0].requirement


def test_DashBoardTemplate_create_online_store_autoupdate_schedule_ok_single_2(mocker):
    return_list: list[str] = ["4:00"]
    m = mocker.patch(
        "common.read_config.get_auto_update_online_store_time", return_value=return_list
    )
    ret_list = admin.DashBoardTemplate.create_online_store_autoupdate_schedule()
    assert len(ret_list) == 1
    assert "04:00" == ret_list[0].requirement


def test_DashBoardTemplate_create_online_store_autoupdate_schedule_ok_multi(mocker):
    return_list: list[str] = ["01:20", "12:51", "21:35"]
    m = mocker.patch(
        "common.read_config.get_auto_update_online_store_time", return_value=return_list
    )
    ret_list = admin.DashBoardTemplate.create_online_store_autoupdate_schedule()
    assert len(ret_list) == 3
    for ret, conf in zip(ret_list, return_list):
        assert ret.requirement == conf


def test_DashBoardTemplate_is_auto_copy_online_store_to_local_true(mocker):
    return_dict: dict = {"auto": True, "type": "overwrite"}
    m = mocker.patch(
        "common.read_config.get_auto_copy_of_online_store_info_to_local",
        return_value=return_dict,
    )
    ret = admin.DashBoardTemplate.is_auto_copy_online_store_to_local()
    assert ret == True


def test_DashBoardTemplate_is_auto_copy_online_store_to_local_false_none(mocker):
    return_dict = None
    m = mocker.patch(
        "common.read_config.get_auto_copy_of_online_store_info_to_local",
        return_value=return_dict,
    )
    ret = admin.DashBoardTemplate.is_auto_copy_online_store_to_local()
    assert ret == False


def test_DashBoardTemplate_is_auto_copy_online_store_to_local_false_blank_dict(mocker):
    return_dict: dict = {}
    m = mocker.patch(
        "common.read_config.get_auto_copy_of_online_store_info_to_local",
        return_value=return_dict,
    )
    ret = admin.DashBoardTemplate.is_auto_copy_online_store_to_local()
    assert ret == False


def test_DashBoardTemplate_is_auto_copy_online_store_to_local_false_setting_false(
    mocker,
):
    return_dict: dict = {"auto": False, "type": "overwrite"}
    m = mocker.patch(
        "common.read_config.get_auto_copy_of_online_store_info_to_local",
        return_value=return_dict,
    )
    ret = admin.DashBoardTemplate.is_auto_copy_online_store_to_local()
    assert ret == False


def test_DashBoardTemplate_get_auto_copy_online_store_to_local_internal_config_overwrite(
    mocker,
):
    return_dict: dict = {"auto": True, "type": "overwrite"}
    m = mocker.patch(
        "common.read_config.get_auto_copy_of_online_store_info_to_local",
        return_value=return_dict,
    )
    ret = admin.DashBoardTemplate.get_auto_copy_online_store_to_local_internal_config()
    assert ret == {
        "name": "コピータイプ",
        "value": filter_name.OnlineStoreCopyTypeName.OVERWRITE.jname,
    }


def test_DashBoardTemplate_get_auto_copy_online_store_to_local_internal_config_fill_blank(
    mocker,
):
    return_dict: dict = {"auto": True, "type": "fill_blank"}
    m = mocker.patch(
        "common.read_config.get_auto_copy_of_online_store_info_to_local",
        return_value=return_dict,
    )
    ret = admin.DashBoardTemplate.get_auto_copy_online_store_to_local_internal_config()
    assert ret == {
        "name": "コピータイプ",
        "value": filter_name.OnlineStoreCopyTypeName.FILL_BLANK.jname,
    }


def test_DashBoardTemplate_get_auto_copy_online_store_to_local_internal_config_fill_blank_no_under_bar(
    mocker,
):
    return_dict: dict = {"auto": True, "type": "fillblank"}
    m = mocker.patch(
        "common.read_config.get_auto_copy_of_online_store_info_to_local",
        return_value=return_dict,
    )
    ret = admin.DashBoardTemplate.get_auto_copy_online_store_to_local_internal_config()
    assert ret == {
        "name": "コピータイプ",
        "value": filter_name.OnlineStoreCopyTypeName.FILL_BLANK.jname,
    }


def test_DashBoardTemplate_get_auto_copy_online_store_to_local_internal_config_no_type(
    mocker,
):
    return_dict: dict = {"auto": True, "type": ""}
    m = mocker.patch(
        "common.read_config.get_auto_copy_of_online_store_info_to_local",
        return_value=return_dict,
    )
    ret = admin.DashBoardTemplate.get_auto_copy_online_store_to_local_internal_config()
    assert ret == {}

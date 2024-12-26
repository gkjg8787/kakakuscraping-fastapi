from fastapi.testclient import TestClient

from main import app
from common import filter_name


client = TestClient(app)
prefix = "/search"
title = "外部サイト検索"


def test_read_search_top():
    response = client.get(
        f"{prefix}/",
    )
    assert response.status_code == 200
    assert title in response.text


def test_read_search_top_option_hide_safes(mocker):
    mock_config = {"SAFES": {"DISPLAY": "OFF"}}
    mocker.patch(
        "common.read_config.get_search_options_default", return_value=mock_config
    )
    response = client.get(
        f"{prefix}/",
    )
    assert response.status_code == 200
    assert title in response.text
    assert "SafeSearch OFF" not in response.text


def test_read_search_top_option_checked_safes_off(mocker):
    mock_config = {"SAFES": {"DISPLAY": "ON", "INIT": "OFF"}}
    mocker.patch(
        "common.read_config.get_search_options_default", return_value=mock_config
    )
    response = client.get(
        f"{prefix}/",
    )
    assert response.status_code == 200
    assert (
        '<input type="checkbox" name="safes" form="search_inputform" id="safe_search_checkbox" value="0" checked>'
        in response.text
    )


def test_read_search_top_option_no_check_zaiko(mocker):
    mock_config = {"ZAIKO": {"INIT": "OFF"}}
    mocker.patch(
        "common.read_config.get_search_options_default", return_value=mock_config
    )
    response = client.get(
        f"{prefix}/",
    )
    assert response.status_code == 200
    assert (
        '<input type="checkbox" name="zaiko" form="search_inputform" id="zaiko_checkbox" value="1" >'
        in response.text
    )


def test_read_search_top_option_checked_zaiko(mocker):
    mock_config = {"ZAIKO": {"INIT": "ON"}}
    mocker.patch(
        "common.read_config.get_search_options_default", return_value=mock_config
    )
    response = client.get(
        f"{prefix}/",
    )
    assert response.status_code == 200
    assert (
        '<input type="checkbox" name="zaiko" form="search_inputform" id="zaiko_checkbox" value="1" checked>'
        in response.text
    )


def test_read_search_top_option_no_check_listview(mocker):
    mock_config = {"LISTVIEW": {"INIT": "OFF"}}
    mocker.patch(
        "common.read_config.get_search_options_default", return_value=mock_config
    )
    response = client.get(
        f"{prefix}/",
    )
    assert response.status_code == 200
    assert (
        '<input type="checkbox" name="listview" form="search_inputform" id="listview_checkbox" value="1" >'
        in response.text
    )


def test_read_search_top_option_checked_listview(mocker):
    mock_config = {"LISTVIEW": {"INIT": "ON"}}
    mocker.patch(
        "common.read_config.get_search_options_default", return_value=mock_config
    )
    response = client.get(
        f"{prefix}/",
    )
    assert response.status_code == 200
    assert (
        '<input type="checkbox" name="listview" form="search_inputform" id="listview_checkbox" value="1" checked>'
        in response.text
    )


def test_read_search_top_option_category_selected_game(mocker):
    mock_config = {"CATEGORY": {"VALUE": "ゲーム"}}
    mocker.patch(
        "common.read_config.get_search_options_default", return_value=mock_config
    )
    response = client.get(
        f"{prefix}/",
    )
    assert response.status_code == 200
    assert '<option value="2" selected>ゲーム</option>' in response.text


def test_read_search_top_option_no_check_store(mocker):
    mock_config = {}
    mocker.patch(
        "common.read_config.get_search_options_default", return_value=mock_config
    )
    response = client.get(
        f"{prefix}/",
    )
    assert response.status_code == 200
    assert '<input type="checkbox" name="store" value="1" >' in response.text
    assert '<input type="checkbox" name="store" value="2" >' in response.text
    assert '<input type="checkbox" name="store" value="3" >' in response.text


def test_read_search_top_option_checked_store_bookoff(mocker):
    mock_config = {"STORE": {"ブックオフ": "ON"}}
    mocker.patch(
        "common.read_config.get_search_options_default", return_value=mock_config
    )
    response = client.get(
        f"{prefix}/",
    )
    assert response.status_code == 200
    assert '<input type="checkbox" name="store" value="1" >' in response.text
    assert '<input type="checkbox" name="store" value="2" checked>' in response.text
    assert '<input type="checkbox" name="store" value="3" >' in response.text


def test_read_search_top_option_checked_store_surugaya_netoff(mocker):
    mock_config = {
        "STORE": {
            "駿河屋": "ON",
            "ブックオフ": "OFF",
            "ネットオフ": "ON",
        }
    }
    mocker.patch(
        "common.read_config.get_search_options_default", return_value=mock_config
    )
    response = client.get(
        f"{prefix}/",
    )
    assert response.status_code == 200
    assert '<input type="checkbox" name="store" value="1" checked>' in response.text
    assert '<input type="checkbox" name="store" value="2" >' in response.text
    assert '<input type="checkbox" name="store" value="3" checked>' in response.text


def test_read_search_search():
    params = {
        filter_name.FilterQueryName.WORD.value: "Python",
    }
    response = client.get(
        f"{prefix}/",
        params=params,
    )
    assert response.status_code == 200
    assert title in response.text
    assert '<div class="itembox">' in response.text


def test_read_search_add_no_data():
    response = client.post(
        f"{prefix}/add/",
    )
    assert response.status_code == 200
    assert "検索アイテム追加" in response.text
    assert "URLが不明です" in response.text


def test_read_search_add_no_support_url():
    response = client.post(
        f"{prefix}/add/",
        data={
            filter_name.TemplatePostName.ITEM_NAME.value: "google",
            filter_name.TemplatePostName.URL_PATH.value: "https://www.google.com",
            filter_name.TemplatePostName.SEARCH_QUERY.value: "?word=Python",
        },
    )
    assert response.status_code == 200
    assert "検索アイテム追加" in response.text
    assert "対象外のURLです" in response.text


def test_read_search_add_add_item():
    SURUGAYA_PRODUCT_PYTHON_URL = "https://www.suruga-ya.jp/product/detail/BO3992059"
    SURUGAYA_PRODUCT_TITLE = "生成AI・ChatGPTでPythonプログラミング"

    response = client.post(
        f"{prefix}/add/",
        data={
            filter_name.TemplatePostName.ITEM_NAME.value: SURUGAYA_PRODUCT_TITLE,
            filter_name.TemplatePostName.URL_PATH.value: SURUGAYA_PRODUCT_PYTHON_URL,
            filter_name.TemplatePostName.SEARCH_QUERY.value: "?word=Python",
        },
    )
    assert response.status_code == 200
    assert "検索アイテム追加" in response.text
    assert SURUGAYA_PRODUCT_PYTHON_URL in response.text
    assert SURUGAYA_PRODUCT_TITLE in response.text

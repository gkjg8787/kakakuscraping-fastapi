
from fastapi.testclient import TestClient

from main import app
from common import filter_name


client = TestClient(app)
prefix = '/search'

def test_read_search_top():
    response = client.get(
        f'{prefix}/',
    )
    assert response.status_code == 200
    assert '外部サイト検索' in response.text

def test_read_search_search():
    params = {
        filter_name.FilterQueryName.WORD.value:"Python",
    }
    response = client.get(
        f'{prefix}/',
        params=params,
    )
    assert response.status_code == 200
    assert '外部サイト検索' in response.text
    assert '<div class="itembox">' in response.text

def test_read_search_add_no_data():
    response = client.post(
        f'{prefix}/add/',
    )
    assert response.status_code == 200
    assert '検索アイテム追加' in response.text
    assert 'URLが不明です' in response.text

def test_read_search_add_no_support_url():
    response = client.post(
        f'{prefix}/add/',
        data={
            filter_name.TemplatePostName.ITEM_NAME.value:"google",
            filter_name.TemplatePostName.URL_PATH.value:"https://www.google.com",
            filter_name.TemplatePostName.SEARCH_QUERY.value:"?word=Python"
        }
    )
    assert response.status_code == 200
    assert '検索アイテム追加' in response.text
    assert '対象外のURLです' in response.text

def test_read_search_add_add_item():
    SURUGAYA_PRODUCT_PYTHON_URL = "https://www.suruga-ya.jp/product/detail/BO3992059"
    SURUGAYA_PRODUCT_TITLE = "生成AI・ChatGPTでPythonプログラミング"
    
    response = client.post(
        f'{prefix}/add/',
        data={
            filter_name.TemplatePostName.ITEM_NAME.value:SURUGAYA_PRODUCT_TITLE,
            filter_name.TemplatePostName.URL_PATH.value:SURUGAYA_PRODUCT_PYTHON_URL,
            filter_name.TemplatePostName.SEARCH_QUERY.value:"?word=Python"
        }
    )
    assert response.status_code == 200
    assert '検索アイテム追加' in response.text
    assert SURUGAYA_PRODUCT_PYTHON_URL in response.text
    assert SURUGAYA_PRODUCT_TITLE in response.text

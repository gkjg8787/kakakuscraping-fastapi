from fastapi.testclient import TestClient

from main import app
from common import filter_name
import common.util as cmn_util

from tests.test_db import test_db, drop_test_db
from tests.test_routers.test_common import (
    RedirectCheckValue,
    check_redirect,
    is_html,
)
from tests.test_sqlalchemy import (
    insert_pricelog_sync,
)

from tests.test_accessor import db_test_data
from analysis.database_analysis import LogAnalysisError
from proc import system_status

client = TestClient(app)
prefix = '/users'

SURUGAYA_PRODUCT_NAUSHIKA="https://www.suruga-ya.jp/product/detail/128010205"
SURUGAYA_OTHER_NAUSHIKA="https://www.suruga-ya.jp/product-other/128010205"

REDIRECT_READ_USERS = RedirectCheckValue(status_code=302, location=prefix)

def test_read_root(test_db):
    response = client.get('/')
    check_redirect(response, [ RedirectCheckValue(status_code=302, location=prefix) ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users():
    response = client.get(f'{prefix}/')
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_filter_clear():
    response = client.get(f'{prefix}/fc/')
    check_redirect(response, [ RedirectCheckValue(status_code=302, location=prefix) ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_items_add():
    response = client.get(f'{prefix}/items/add/')
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_items_add_post_no_data(test_db):
    response = client.post(
        f'{prefix}/items/add/result/',
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "アイテム名かURLを入力してください" in response.text

def test_read_users_items_add_post_not_support_url(test_db):
    response = client.post(
        f'{prefix}/items/add/result/',
        data={filter_name.TemplatePostName.URL_PATH.value:'https://www.google.com'},
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "対象外のURLです" in response.text

def add_item_name_success():
    response = client.post(
        f'{prefix}/items/add/result/',
        data={filter_name.TemplatePostName.ITEM_NAME.value:'test_item'},
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "登録しました。" in response.text

def add_item_url_only_success():
    response = client.post(
        f'{prefix}/items/add/result/',
        data={filter_name.TemplatePostName.URL_PATH.value:SURUGAYA_PRODUCT_NAUSHIKA},
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "登録しました。" in response.text

def add_item_name_and_url_success():
    response = client.post(
        f'{prefix}/items/add/result/',
        data={
            filter_name.TemplatePostName.ITEM_NAME.value:'full regist item',
            filter_name.TemplatePostName.URL_PATH.value:SURUGAYA_PRODUCT_NAUSHIKA
            },
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "登録しました。" in response.text

def test_read_users_items_add_post_add_item_name(test_db):
    add_item_name_success()
    drop_test_db()

def test_read_users_items_add_post_add_url(test_db):
    add_item_url_only_success()
    drop_test_db()

def test_read_users_items_add_post_add_item_name_and_url(test_db):
    add_item_name_and_url_success()
    drop_test_db()

def test_read_users_items_update_all_no_data(test_db):
    response = client.post(
        f'{prefix}/items/updates/',
        )
    assert response.status_code == 422

def test_read_users_items_update_all_no_backserver(test_db):
    response = client.post(
        f'{prefix}/items/updates/',
        data={'item_all_update':filter_name.ItemUpdateValue.ITEM_ALL_UPDATE},
        )
    assert response.status_code == 200
    is_html(response.text)
    assert '更新できない状態です。' in response.text


def test_read_users_url_update_no_backserver(test_db):
    response = client.post(
        f'{prefix}/items/v/update/',
        )
    assert response.status_code == 200
    is_html(response.text)
    assert '更新できない状態です。' in response.text

def test_read_users_items_update_no_backserver(test_db):
    response = client.post(
        f'{prefix}/items/v/update/all/',
        )
    assert response.status_code == 200
    is_html(response.text)
    assert '更新できない状態です。' in response.text

def test_read_users_items_view_no_query(test_db):
    response = client.get(f'{prefix}/items/v/')
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_items_view_exist_item(test_db):
    add_item_name_success()

    params = {filter_name.ItemDetailQueryName.ITEMID.value:1}
    response = client.get(f'{prefix}/items/v/', params=params)
    assert response.status_code == 200
    is_html(response.text)

    drop_test_db()

def test_read_users_items_add_url_no_data(test_db):
    response = client.post(
        f'{prefix}/items/v/addurl/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_items_add_url_item_id(test_db):
    response = client.post(
        f'{prefix}/items/v/addurl/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1}
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "追加URL" in response.text
    assert "送信" in response.text

def test_read_users_items_add_url_result_no_data(test_db):
    response = client.post(
        f'{prefix}/items/v/addurl/result/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_items_add_url_result_not_exist_item_id(test_db):
    response = client.post(
        f'{prefix}/items/v/addurl/result/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1}
        )
    assert response.status_code == 200
    is_html(response.text)
    assert 'アイテムが見つかりません' in response.text

def test_read_users_items_add_url_result_no_support_url(test_db):
    add_item_name_success()

    response = client.post(
        f'{prefix}/items/v/addurl/result/',
        data={
            filter_name.TemplatePostName.ITEM_ID.value:1,
            filter_name.TemplatePostName.URL_PATH.value:"https://www.google.com", 
            },
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "対象外のURLです" in response.text

    drop_test_db()

def test_read_users_items_add_result_url_add_url(test_db):
    add_item_name_and_url_success()

    response = client.post(
        f'{prefix}/items/v/addurl/result/',
        data={
            filter_name.TemplatePostName.ITEM_ID.value:1,
            filter_name.TemplatePostName.URL_PATH.value:SURUGAYA_OTHER_NAUSHIKA, 
            },
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "登録しました。" in response.text

    drop_test_db()

def test_read_users_items_add_result_url_add_url_search_query(test_db):
    add_item_name_and_url_success()

    response = client.post(
        f'{prefix}/items/v/addurl/result/',
        data={
            filter_name.TemplatePostName.ITEM_ID.value:1,
            filter_name.TemplatePostName.URL_PATH.value:SURUGAYA_OTHER_NAUSHIKA, 
            filter_name.TemplatePostName.SEARCH_QUERY.value:"?word=test",
            },
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "登録しました。" in response.text
    assert "/search/?word=test" in response.text
    drop_test_db()

def test_read_users_items_update_item_name_no_data(test_db):
    response = client.post(
        f'{prefix}/items/v/name/update/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_items_update_item_name_not_exist_item_id(test_db):
    response = client.post(
        f'{prefix}/items/v/name/update/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1}
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "アイテムが見つかりません" in response.text

def test_read_users_items_update_item_name_result_no_data(test_db):
    response = client.post(
        f'{prefix}/items/v/name/update/result/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_items_update_item_name_result_range_out_of_range_item_name(test_db):
    add_item_name_and_url_success()

    response = client.post(
        f'{prefix}/items/v/name/update/result/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1,
              filter_name.TemplatePostName.ITEM_NAME.value:"",
              }
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "アイテム名は1文字以上入れて下さい" in response.text
    drop_test_db()

def test_read_users_items_update_item_name_result_range_change_name(test_db):
    add_item_name_and_url_success()

    response = client.post(
        f'{prefix}/items/v/name/update/result/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1,
              filter_name.TemplatePostName.ITEM_NAME.value:"change test name",
              }
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "変更しました。" in response.text
    drop_test_db()

def test_read_users_items_inact_url_all_no_data(test_db):
    response = client.post(
        f'{prefix}/items/v/url/inact/all/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_items_inact_url_all_inact_all(test_db):
    add_item_name_and_url_success()

    response = client.post(
        f'{prefix}/items/v/url/inact/all/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1}
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "更新しました。" in response.text
    drop_test_db()

def test_read_users_items_inact_url_no_data(test_db):
    response = client.post(
        f'{prefix}/items/v/url/inact/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)


def test_read_users_items_inact_url_inact_all_url(test_db):
    add_item_name_and_url_success()

    response = client.post(
        f'{prefix}/items/v/url/inact/all/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1,
              }
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "更新しました。" in response.text
    drop_test_db()

def test_read_users_items_act_url_no_data(test_db):
    response = client.post(
        f'{prefix}/items/v/url/act/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_items_act_url_not_exist_url(test_db):
    response = client.post(
        f'{prefix}/items/v/url/act/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1,
              }
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "URLが不明です" in response.text

def test_read_users_items_act_url_act_url(test_db):
    add_item_name_and_url_success()

    response = client.post(
        f'{prefix}/items/v/url/act/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1,
              filter_name.TemplatePostName.URL_ID.value:1,
              }
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "更新しました。" in response.text
    drop_test_db()

def test_read_users_items_url_remove_no_data(test_db):
    response = client.post(
        f'{prefix}/items/v/url/remove/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_items_url_remove_no_url_id(test_db):
    response = client.post(
        f'{prefix}/items/v/url/remove/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1,}
    )
    assert response.status_code == 200
    is_html(response.text)
    assert "URLが不明です" in response.text

def test_read_users_items_url_remove_url_remove(test_db):
    add_item_name_and_url_success()

    response = client.post(
        f'{prefix}/items/v/url/remove/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1,
              filter_name.TemplatePostName.URL_ID.value:1,
              }
    )
    assert response.status_code == 200
    is_html(response.text)
    assert "除外しました。" in response.text
    drop_test_db()

def test_read_users_items_view_chart_no_data(test_db):
    response = client.get(
        f'{prefix}/items/v/chart/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def add_once_pricelog(db):
    pldict = {
        'url_id':1,
        'created_at':cmn_util.dbtimeTodatetime('2023-08-15 17:12:03'),
        'uniqname':'test_uniq_name',
        'usedprice':1500,
        'newprice':3000,
        'taxin':True,
        'onsale':False,
        'salename':'',
        'issuccess':True,
        'storename':'駿河屋',
        'trendrate':0.0,
    }
    insert_pricelog_sync(db, pldict)

def test_read_users_items_view_chart_exist_data(test_db):
    add_item_name_and_url_success()
    add_once_pricelog(test_db)

    params = {filter_name.ItemDetailQueryName.ITEMID.value:1}
    response = client.get(
        f'{prefix}/items/v/chart/',
        params=params,
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "価格グラフ" in response.text
    drop_test_db()

def test_read_users_items_remove_no_data(test_db):
    response = client.post(
        f'{prefix}/items/v/remove/',
        )
    assert response.status_code == 404
    assert response.json() == {"detail":"Item not found"}

def test_read_users_items_remove_item_id(test_db):
    add_item_name_and_url_success()
    response = client.post(
        f'{prefix}/items/v/remove/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1},
        )
    assert response.status_code == 200
    is_html(response.text)
    item_name = 'full regist item'
    assert f'本当に{item_name}を削除しますか' in response.text
    drop_test_db()

def test_read_users_items_remove_result_no_data(test_db):
    response = client.post(
        f'{prefix}/items/v/remove/result/',
        )
    assert response.status_code == 404
    assert response.json() == {"detail":"Item not found"}

def test_read_users_items_remove_result_remove_item(test_db):
    add_item_name_and_url_success()
    response = client.post(
        f'{prefix}/items/v/remove/result/',
        data={filter_name.TemplatePostName.ITEM_ID.value:1},
        )
    assert response.status_code == 200
    is_html(response.text)
    assert '削除しました。' in response.text
    drop_test_db()

def test_read_users_groups_add(test_db):
    response = client.get(
        f'{prefix}/groups/add/',
    )
    assert response.status_code == 200
    is_html(response.text)
    assert '<p><input type="submit" value="作成"></p>' in response.text

def test_read_users_groups_add_result_no_data(test_db):
    response = client.post(
        f'{prefix}/groups/add/result/',
        )
    assert response.status_code == 200
    is_html(response.text)
    assert '<p><input type="submit" value="作成"></p>' in response.text

def add_test_group():
    response = client.post(
        f'{prefix}/groups/add/result/',
        data={filter_name.TemplatePostName.GROUP_NAME.value:"test group"},
        )
    assert response.status_code == 200
    is_html(response.text)
    assert '作成しました。' in response.text

def test_read_users_groups_add_result_add_group(test_db):
    add_test_group()
    drop_test_db()

def test_read_users_groups_edit_no_data(test_db):
    response = client.get(
        f'{prefix}/groups/edit/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_groups_edit(test_db):
    add_test_group()
    params = {filter_name.FilterQueryName.GID.value:1}
    response = client.get(
        f'{prefix}/groups/edit/',
        params=params,
        )
    assert response.status_code == 200
    is_html(response.text)
    assert 'グループ編集' in response.text
    drop_test_db()

def test_read_users_groups_edit_update_no_data(test_db):
    response = client.post(
        f'{prefix}/groups/edit/update/',
    )
    check_redirect(response, [ RedirectCheckValue(status_code=302, location="/groups/edit/"), REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200

def test_read_users_groups_edit_update_update_item(test_db):
    add_item_name_and_url_success()
    add_test_group()
    group_item_list = [1]
    response = client.post(
        f'{prefix}/groups/edit/update/',
        data={
            filter_name.TemplatePostName.GROUP_ID.value:1,
            filter_name.TemplatePostName.GROUP_ITEM_LIST.value:group_item_list,
            }
    )
    check_redirect(response, [ RedirectCheckValue(status_code=302, location="/groups/edit/") ])
    assert response.status_code == 200
    drop_test_db()

def test_read_users_groups_edit_update_update_item_list(test_db):
    add_item_name_and_url_success()
    response = client.post(
        f'{prefix}/items/add/result/',
        data={
            filter_name.TemplatePostName.ITEM_NAME.value:'two',
            filter_name.TemplatePostName.URL_PATH.value:SURUGAYA_OTHER_NAUSHIKA
            },
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "登録しました。" in response.text
    add_test_group()
    group_item_list = [1, 2]
    response = client.post(
        f'{prefix}/groups/edit/update/',
        data={
            filter_name.TemplatePostName.GROUP_ID.value:1,
            filter_name.TemplatePostName.GROUP_ITEM_LIST.value:group_item_list,
            }
    )
    check_redirect(response, [ RedirectCheckValue(status_code=302, location="/groups/edit/") ])
    assert response.status_code == 200
    drop_test_db()

def test_read_users_groups_delete_no_data(test_db):
    response = client.post(
        f'{prefix}/groups/delete/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_groups_delete_group_delete(test_db):
    add_test_group()
    response = client.post(
        f'{prefix}/groups/delete/',
        data={filter_name.TemplatePostName.GROUP_ID.value:1},
        )
    assert response.status_code == 200
    is_html(response.text)
    group_name = 'test group'
    assert f'本当に{group_name}を削除しますか？' in response.text
    drop_test_db()

def test_read_users_groups_delete_result_no_data(test_db):
    response = client.post(
        f'{prefix}/groups/delete/result/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_groups_delete_result_no_data(test_db):
    add_test_group()
    response = client.post(
        f'{prefix}/groups/delete/result/',
        data={filter_name.TemplatePostName.GROUP_ID.value:1},
        )
    assert response.status_code == 200
    is_html(response.text)
    assert '削除しました。' in response.text
    drop_test_db()

def test_read_users_groups_rename_no_data(test_db):
    response = client.post(
        f'{prefix}/groups/rename/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS ]) #[ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_groups_rename_rename_group(test_db):
    add_test_group()
    response = client.post(
        f'{prefix}/groups/rename/',
        data={filter_name.TemplatePostName.GROUP_ID.value:1},
        )
    assert response.status_code == 200
    is_html(response.text)
    assert '変更前グループ名' in response.text
    drop_test_db()

def test_read_users_groups_rename_result_no_data(test_db):
    response = client.post(
        f'{prefix}/groups/rename/result/',
        )
    check_redirect(response, [ REDIRECT_READ_USERS, REDIRECT_READ_USERS ])
    assert response.status_code == 200
    is_html(response.text)

def test_read_users_groups_rename_result_rename_group(test_db):
    add_test_group()
    response = client.post(
        f'{prefix}/groups/rename/result/',
        data={filter_name.TemplatePostName.GROUP_ID.value:1,
              filter_name.TemplatePostName.GROUP_NAME.value:"change group name"},
        )
    assert response.status_code == 200
    is_html(response.text)
    group_name = 'change group name'
    assert f'{group_name}に変更しました。' in response.text
    drop_test_db()

def test_read_users_analysis_no_data(test_db):
    response = client.get(f'{prefix}/items/analysis/')
    assert response.status_code == 200
    is_html(response.text)
    assert LogAnalysisError.DATA_IS_ZERO.value in response.text

def test_read_users_analysis_no_log(test_db):
    add_item_name_and_url_success()
    response = client.get(f'{prefix}/items/analysis/')
    assert response.status_code == 200
    is_html(response.text)
    assert LogAnalysisError.DICT_IS_ZERO.value in response.text
    drop_test_db()

def test_read_users_analysis_data_update(test_db, mocker):
    m = mocker.patch("proc.system_status.SystemStatusAccess.getStatus", return_value=system_status.SystemStatus.DATA_UPDATE)
    response = client.get(f'{prefix}/items/analysis/')
    assert response.status_code == 200
    is_html(response.text)
    assert LogAnalysisError.DATA_IS_BEING_UPDATED.value in response.text

def test_read_users_analysis(test_db):
    db_test_data.add_analysis_data_set_1(test_db)
    response = client.get(f'{prefix}/items/analysis/')
    assert response.status_code == 200
    is_html(response.text)
    assert 'URL毎の平均店舗数の変動' in response.text
    drop_test_db()

def test_read_users_urls_view_no_data(test_db):
    response = client.get(f'{prefix}/urls/v/')
    assert response.status_code == 200
    is_html(response.text)
    assert '登録URL一覧' in response.text
    assert '0件' in response.text

def test_read_users_urls_view_one_data(test_db):
    add_item_name_and_url_success()
    response = client.get(f'{prefix}/urls/v/')
    assert response.status_code == 200
    is_html(response.text)
    assert '登録URL一覧' in response.text
    assert '1件' in response.text
    drop_test_db()

def test_read_users_extract(test_db):
    response = client.get(f'{prefix}/ex/')
    assert response.status_code == 200
    is_html(response.text)
    assert 'アイテムを店舗名で抽出' in response.text
    assert '0件' in response.text

def test_read_users_stores(test_db):
    response = client.get(f'{prefix}/stores/')
    assert response.status_code == 200
    is_html(response.text)
    assert '登録店舗一覧' in response.text
    assert '0件' in response.text


def test_read_users_stores_postage_edit(test_db):
    response = client.get(f'{prefix}/stores/postage/edit/')
    assert response.status_code == 200
    is_html(response.text)
    assert '送料条件の編集' in response.text

def create_post_data_for_store_condition(store_id :int,
                                         terms_index :int,
                                         storename : str,
                                         boundary_val :int,
                                         b_ope_val :str,
                                         postage_val :int,
                                         ):
    POST_STORE_NAME = filter_name.ItemCombPostKey.STORENAME
    BOUNDARY = filter_name.ItemCombPostKey.BOUNDARY
    B_OPE = filter_name.ItemCombPostKey.OPE
    POSTAGE = filter_name.ItemCombPostKey.POSTAGE
    results = {
        filter_name.TemplatePostName.ITEM_ID.value:1,
        f"stores[{store_id}][{POST_STORE_NAME}]":storename,
        f"stores[{store_id}][terms][{terms_index}][{BOUNDARY}][]":boundary_val,
        f"stores[{store_id}][terms][{terms_index}][{B_OPE}][]":b_ope_val,
        f"stores[{store_id}][terms][{terms_index}][{POSTAGE}][]":postage_val,
    }

    return results

def create_postage_data_1():
    return create_post_data_for_store_condition(
            store_id=1,
            terms_index=1,
            storename="駿河屋",
            boundary_val=0,
            b_ope_val="ge",
            postage_val=0,
        )

def test_read_users_stores_postage_edit_result_update_delete(test_db):
    db_test_data.add_data_store(test_db)
    db_test_data.add_data_store_postage(test_db)
    response = client.post(
        f'{prefix}/stores/postage/edit/result/',
        data=create_postage_data_1(),
        )
    assert response.status_code == 200
    is_html(response.text)
    assert '送料条件の更新結果' in response.text
    no_space_text = response.text.translate(str.maketrans({'\n':'', ' ':''}))
    assert '<h3>更新</h3><p>件数1件</p>' in no_space_text
    assert '<h3>削除</h3><p>件数3件</p>' in no_space_text

    drop_test_db()

def create_postage_data_2():
    return create_post_data_for_store_condition(
            store_id=3,
            terms_index=1,
            storename="ブックオフ",
            boundary_val=300,
            b_ope_val="ge",
            postage_val=440,
        )

def test_read_users_stores_postage_edit_result_insert_delete(test_db):
    db_test_data.add_data_store(test_db)
    db_test_data.add_data_store_postage(test_db)
    response = client.post(
        f'{prefix}/stores/postage/edit/result/',
        data=create_postage_data_2(),
        )
    assert response.status_code == 200
    is_html(response.text)
    assert '送料条件の更新結果' in response.text
    no_space_text = response.text.translate(str.maketrans({'\n':'', ' ':''}))
    assert '<h3>追加</h3><p>件数1件</p>' in no_space_text
    ''' 削除の件数は店舗数 '''
    assert '<h3>削除</h3><p>件数3件</p>' in no_space_text

    drop_test_db()

def test_read_users_store_delete_no_store(test_db):
    response = client.post(
        f'{prefix}/stores/delete/',
        data={filter_name.TemplatePostName.STORE_ID.value:1}
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "店舗情報の削除" in response.text


def test_read_users_store_delete(test_db):
    db_test_data.add_data_store(test_db)
    db_test_data.add_data_store_postage(test_db)
    response = client.post(
        f'{prefix}/stores/delete/',
        data={filter_name.TemplatePostName.STORE_ID.value:1}
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "店舗情報の削除" in response.text
    storename = "駿河屋"
    assert f"本当に{storename}の情報を削除しますか" in response.text
    drop_test_db()

def test_read_users_store_delete_result(test_db):
    db_test_data.add_data_store(test_db)
    db_test_data.add_data_store_postage(test_db)
    response = client.post(
        f'{prefix}/stores/delete/result/',
        data={filter_name.TemplatePostName.STORE_ID.value:1}
        )
    assert response.status_code == 200
    is_html(response.text)
    assert "店舗情報の削除" in response.text
    assert "削除しました。" in response.text
    drop_test_db()

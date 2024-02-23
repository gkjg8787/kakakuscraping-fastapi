from proc import getAndWrite
from tests.test_db import test_db


def test_startParse_filenotfound(mocker, test_db, capfd):
    m0 = mocker.patch("accessor.item.item.UrlQuery.add_url", return_value=1)
    m1 = mocker.patch("proc.getAndWrite.get_parse_data", side_effect=FileNotFoundError)
    m2 = mocker.patch("proc.getAndWrite.update_itemsprices", return_value=None)
    m3 = mocker.patch("proc.getAndWrite.update_online_storepostage", return_value=None)
    m4 = mocker.patch(
        "proc.getAndWrite.update_makepure_postage_shop_list", return_value=None
    )
    m5 = mocker.patch("proc.getAndWrite.deleteTempFile", return_value=None)
    url = "test"
    fname = "test.text"
    item_id = -1
    getAndWrite.startParse(db=test_db, url=url, fname=fname, item_id=item_id)
    captured = capfd.readouterr()
    assert "FileNotFoundError" in captured.out
    assert f"fname={fname}" in captured.out


def test_startParse_attributeerror(mocker, test_db, capfd):
    m0 = mocker.patch("accessor.item.item.UrlQuery.add_url", return_value=1)
    m1 = mocker.patch("proc.getAndWrite.get_parse_data", side_effect=AttributeError)
    m2 = mocker.patch("proc.getAndWrite.update_itemsprices", return_value=None)
    m3 = mocker.patch("proc.getAndWrite.update_online_storepostage", return_value=None)
    m4 = mocker.patch(
        "proc.getAndWrite.update_makepure_postage_shop_list", return_value=None
    )
    m5 = mocker.patch("proc.getAndWrite.deleteTempFile", return_value=None)
    url = "test"
    fname = "test.text"
    item_id = -1
    getAndWrite.startParse(db=test_db, url=url, fname=fname, item_id=item_id)
    captured = capfd.readouterr()
    assert "AttributeError" in captured.out
    assert f"url={url}" in captured.out

import sys
import logging

import pytest

from common import cmnlog
from proc import online_store_postage as osp
from itemcomb import prefecture
from tests.test_db import test_db


@pytest.fixture
def loginit():
    logger = logging.getLogger(cmnlog.LogName.MANAGER)
    h = logging.StreamHandler(stream=sys.stdout)
    h.setFormatter(logging.Formatter(fmt="%(levelname)s - %(message)s"))
    logger.setLevel(logging.DEBUG)
    logger.addHandler(h)
    yield
    del logging.Logger.manager.loggerDict[logger.name]


def test_get_db_data_by_pref_id_one_list(test_db):
    pref_id = 1
    db_dict_list = [
        {"pref_id": 1, "boundary": "0<=:1500>", "postage": 300, "terms_id": 1},
    ]
    ret = osp.get_db_data_by_pref_id(pref_id=pref_id, db_dict_list=db_dict_list)
    assert ret == [db_dict_list[0]]


def test_get_db_data_by_pref_id_multi(test_db):
    pref_id = 2
    db_dict_list = [
        {"pref_id": 1, "boundary": "0<=:1500>", "postage": 300, "terms_id": 1},
        {"pref_id": 2, "boundary": "0<=", "postage": 500, "terms_id": 1},
        {"pref_id": 10, "boundary": ">2000", "postage": 350, "terms_id": 2},
    ]
    ret = osp.get_db_data_by_pref_id(pref_id=pref_id, db_dict_list=db_dict_list)
    assert ret == [db_dict_list[1]]


def test_get_db_data_by_pref_id_multi_2(test_db):
    pref_id = 2
    db_dict_list = [
        {"pref_id": 1, "boundary": "0<=:1500>", "postage": 300, "terms_id": 1},
        {"pref_id": 2, "boundary": "0<=", "postage": 500, "terms_id": 1},
        {"pref_id": 2, "boundary": ">2000", "postage": 350, "terms_id": 2},
    ]
    ret = osp.get_db_data_by_pref_id(pref_id=pref_id, db_dict_list=db_dict_list)
    assert ret == db_dict_list[1:]


def test_get_terms_id_of_same_terms_equal(test_db):
    db_dict_list = [
        {"pref_id": 1, "boundary": "0<=:1500>", "postage": 300, "terms_id": 1},
    ]
    boundary = "0<=:1500>"
    postage = 300
    ret = osp.get_terms_id_of_same_terms(
        db_dict_list=db_dict_list, boundary=boundary, postage=postage
    )
    assert ret == db_dict_list[0]["terms_id"]


def test_get_terms_id_of_same_terms_not_equal(test_db):
    db_dict_list = [
        {"pref_id": 1, "boundary": "0<=:1500>", "postage": 300, "terms_id": 1},
        {"pref_id": 1, "boundary": "1500<=", "postage": 0, "terms_id": 2},
    ]
    boundary = "0<=:2000>"
    postage = 300
    ret = osp.get_terms_id_of_same_terms(
        db_dict_list=db_dict_list, boundary=boundary, postage=postage
    )
    assert ret is None


class PrefInfoMock:
    def __init__(self):
        pref_names = [prefecture.PrefectureName.get_country_wide_name()]
        pref_names.extend(prefecture.PrefectureName.get_all_prefecturename())
        self.id_to_name = {}
        self.name_to_id = {}
        for id, name in enumerate(pref_names, 1):
            self.id_to_name[id] = name
            self.name_to_id[name] = id

    def get_name(self, id: int):
        return self.id_to_name[id]

    def get_id(self, name: str):
        return self.name_to_id[name]


def test_needs_update_by_campaign_msg_no_campaign(test_db):
    db_dict_list = [
        {"pref_id": 1, "campaign_msg": ""},
    ]
    ret = osp.needs_update_by_campaign_msg(
        db_list=db_dict_list, prefinfo=PrefInfoMock()
    )
    assert ret == True


def test_needs_update_by_campaign_msg_range_campaign(test_db):
    db_dict_list = [
        {
            "pref_id": 1,
            "campaign_msg": "2,000円以上お買い上げで送料無料キャンペーン 2024/01/03 00:00 ～ 2024/01/31 23:59 2,000円未満 500～1,500円 2,000円以上 送料無料",
        },
        {"pref_id": 1, "campaign_msg": ""},
    ]
    ret = osp.needs_update_by_campaign_msg(
        db_list=db_dict_list, prefinfo=PrefInfoMock()
    )
    assert ret == True


def test_needs_update_by_campaign_msg_fix_campaign(test_db):
    db_dict_list = [
        {"pref_id": 1, "campaign_msg": ""},
        {
            "pref_id": 1,
            "campaign_msg": "送料キャンペーン 2024/01/01 00:00 ～ 2024/01/31 23:59 100円未満 700円 10,000円未満 400円 10,000円以上 送料無料",
        },
    ]
    ret = osp.needs_update_by_campaign_msg(
        db_list=db_dict_list, prefinfo=PrefInfoMock()
    )
    assert ret == False


def test_needs_update_by_campaign_msg_fix_campaign_not_common(test_db):
    db_dict_list = [
        {
            "pref_id": 2,
            "campaign_msg": "送料キャンペーン 2024/01/01 00:00 ～ 2024/01/31 23:59 100円未満 700円 10,000円未満 400円 10,000円以上 送料無料",
        },
        {"pref_id": 1, "campaign_msg": ""},
    ]
    ret = osp.needs_update_by_campaign_msg(
        db_list=db_dict_list, prefinfo=PrefInfoMock()
    )
    assert ret == True


def test_needs_update_by_campaign_msg_no_list(mocker, test_db):
    db_dict_list = []
    ret = osp.needs_update_by_campaign_msg(
        db_list=db_dict_list, prefinfo=PrefInfoMock()
    )
    assert ret == True

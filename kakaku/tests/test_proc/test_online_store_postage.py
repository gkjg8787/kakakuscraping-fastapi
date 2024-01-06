import sys
import logging

import pytest

from common import cmnlog
from proc import online_store_postage as osp
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
        {"pref_id":1, "boundary":"0<=:1500>", "postage":300, "terms_id":1 },
    ]
    ret = osp.get_db_data_by_pref_id(
                            pref_id=pref_id,
                            db_dict_list=db_dict_list
                        )
    assert ret == [db_dict_list[0]]

def test_get_db_data_by_pref_id_multi(test_db):
    pref_id = 2
    db_dict_list = [
        {"pref_id":1, "boundary":"0<=:1500>", "postage":300, "terms_id":1 },
        {"pref_id":2, "boundary":"0<=", "postage":500, "terms_id":1 },
        {"pref_id":10, "boundary":">2000", "postage":350, "terms_id":2 },
    ]
    ret = osp.get_db_data_by_pref_id(
                            pref_id=pref_id,
                            db_dict_list=db_dict_list
                        )
    assert ret == [db_dict_list[1]]

def test_get_db_data_by_pref_id_multi_2(test_db):
    pref_id = 2
    db_dict_list = [
        {"pref_id":1, "boundary":"0<=:1500>", "postage":300, "terms_id":1 },
        {"pref_id":2, "boundary":"0<=", "postage":500, "terms_id":1 },
        {"pref_id":2, "boundary":">2000", "postage":350, "terms_id":2 },
    ]
    ret = osp.get_db_data_by_pref_id(
                            pref_id=pref_id,
                            db_dict_list=db_dict_list
                        )
    assert ret == db_dict_list[1:]

def test_get_terms_id_of_same_terms_equal(test_db):
    db_dict_list = [
        {"pref_id":1, "boundary":"0<=:1500>", "postage":300, "terms_id":1 },
    ]
    boundary = "0<=:1500>"
    postage = 300
    ret = osp.get_terms_id_of_same_terms(
                            db_dict_list=db_dict_list,
                            boundary=boundary,
                            postage=postage
                        )
    assert ret == db_dict_list[0]["terms_id"]

def test_get_terms_id_of_same_terms_not_equal(test_db):
    db_dict_list = [
        {"pref_id":1, "boundary":"0<=:1500>", "postage":300, "terms_id":1 },
        {"pref_id":1, "boundary":"1500<=", "postage":0, "terms_id":2 },
    ]
    boundary = "0<=:2000>"
    postage = 300
    ret = osp.get_terms_id_of_same_terms(
                            db_dict_list=db_dict_list,
                            boundary=boundary,
                            postage=postage
                        )
    assert ret is None
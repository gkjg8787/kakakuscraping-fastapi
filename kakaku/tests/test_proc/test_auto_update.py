import sys
import logging
from datetime import datetime, timedelta, timezone

import pytest

from common import cmnlog
from common import util as cmn_util
from proc import auto_update

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


def test_DailyLogOrganizer_run_today(mocker):
    m = mocker.patch("proc.auto_update.scm.sendTask", return_value=0)
    logger = cmnlog.getLogger(cmnlog.LogName.MANAGER)
    dlo = auto_update.DailyLogOrganizer(logger=logger)
    start = dlo.starttime
    dlo.run()
    end = dlo.starttime
    assert cmn_util.isLocalToday(cmn_util.utcTolocaltime(dlo.starttime))
    assert start == end


def test_dailyLogOriganizer_run_yesterday(mocker):
    m = mocker.patch("proc.auto_update.scm.sendTask", return_value=0)
    logger = cmnlog.getLogger(cmnlog.LogName.MANAGER)
    dlo = auto_update.DailyLogOrganizer(logger=logger)
    dlo.starttime = datetime.now(timezone.utc) - timedelta(days=1)
    start = dlo.starttime
    assert not cmn_util.isLocalToday(cmn_util.utcTolocaltime(dlo.starttime))
    dlo.run()
    end = dlo.starttime
    assert cmn_util.isLocalToday(cmn_util.utcTolocaltime(dlo.starttime))
    assert start != end

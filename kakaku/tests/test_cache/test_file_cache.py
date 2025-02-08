import time
import datetime

from cache import file_cache
from common import read_config, util as cm_util


class TestFileCache:
    def test_expireHashData_cache_time(self, tmp_path):
        param = {
            "cachedir": tmp_path,
            "cache_max_num": 2,
            "cache_time": 3,
            "group": "test",
            "span_over_days": True,
        }
        title = "test_expire"
        fc = file_cache.FileCache(**param)
        fc.write(title=title, value="test01")
        assert not fc.expireHashData(title=title)
        time.sleep(3)
        assert fc.expireHashData(title=title)

    def test_expireHashData_not_span_over_days_over_day(self, mocker, tmp_path):
        param = {
            "cachedir": tmp_path,
            "cache_max_num": 2,
            "cache_time": 10,
            "group": "test",
            "span_over_days": False,
        }
        title = "test_expire"
        fc = file_cache.FileCache(**param)
        fc.write(title=title, value="test01")
        assert not fc.expireHashData(title=title)
        now = datetime.datetime.now(datetime.timezone.utc)
        now = cm_util.utcTolocaltime(now)
        yesterday_utime = (now - datetime.timedelta(days=1)).timestamp()
        mocker.patch(
            "cache.file_cache.FileCache.getHashFileTimeStamp",
            return_value=yesterday_utime,
        )
        assert fc.expireHashData(title=title)

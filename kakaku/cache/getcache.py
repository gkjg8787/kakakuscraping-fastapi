from common import read_config
from cache import file_cache


def isSearchCacheFunc():
    b = read_config.is_search_cache()
    if is_True(b):
        return True
    else:
        return False


def is_True(b) -> bool:
    if type(b) is str:
        if b == "True" or b == "true":
            return True
        else:
            return False
    elif type(b) is bool:
        return b
    return False


def getSearchCache():
    return getCache(group="search")


def getCache(
    cachedir: str = "",
    cache_max_num: int | None = None,
    cache_time: int | None = None,
    group: str = "",
    span_over_days: bool = True,
):
    if not cachedir:
        cachedir = read_config.get_dl_temp_dir()
    if not cache_max_num:
        cache_max_num = int(read_config.get_cache_max_num())
    if not cache_time:
        cache_time = int(read_config.get_cache_time())
    return file_cache.FileCache(
        chachedir=cachedir,
        cache_max_num=cache_max_num,
        cache_time=cache_time,
        group=group,
        span_over_days=span_over_days,
    )

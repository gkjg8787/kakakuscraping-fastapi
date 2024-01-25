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
    return getCache("search")


def getCache(group=""):
    return file_cache.FileCache(group)

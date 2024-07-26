from enum import auto
from common.filter_name import AutoLowerName


class NewestCookie(AutoLowerName):
    cfilter_str = auto()


class ItemComb(AutoLowerName):
    pre_select_ids = auto()

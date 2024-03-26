from enum import Enum


class ItemCombError(Enum):
    NO_STORE_DATA = "店舗がありません"
    NO_TODAY_LOG = "本日分のログがありません"

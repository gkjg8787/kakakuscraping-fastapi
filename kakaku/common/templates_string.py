from enum import Enum, auto


class AutoLowerName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class HTMLOption(Enum):
    SELECTED = "selected"
    CHECKED = "checked"


class ItemCombSelectValue(Enum):
    NO_SELECTED = "未選択"


class FormMethod(AutoLowerName):
    GET = auto()
    POST = auto()

from datetime import datetime

from pydantic import BaseModel

from common import templates_string


class SelectOption(BaseModel):
    id: int
    selected: str = ""
    text: str = ""


class Select(BaseModel):
    title: str
    input_name: str
    menu_list: list[SelectOption] = []


class Form(BaseModel):
    method: str = templates_string.FormMethod.GET.value
    action: str = ""


class CheckBoxElement(BaseModel):
    id: int
    text: str = ""
    checked: str = ""


class CheckBox(BaseModel):
    input_name: str
    checkboxes: list[CheckBoxElement] = []


class SelectForm(BaseModel):
    form: Form
    select: Select


class DateInput(BaseModel):
    input_name: str
    min_value: str
    max_value: str
    value: str


class RangeInput(BaseModel):
    title: str
    submit_value: str
    lower: DateInput
    upper: DateInput


class RangeInputForm(BaseModel):
    form: Form
    range_input: RangeInput

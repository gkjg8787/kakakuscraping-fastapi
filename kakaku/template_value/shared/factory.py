from datetime import datetime

from common.filter_name import FilterQueryName
from common import templates_string
from common.util import utcTolocaltime
from . import shared


class DateInputFactory:
    @classmethod
    def create(
        cls,
        input_name: str = "",
        min_value: datetime | None = None,
        max_value: datetime | None = None,
        value: str = "",
    ) -> shared.DateInput:
        min_value_str = ""
        max_value_str = ""
        datefmt = "%Y-%m-%d"
        if min_value and type(min_value) is datetime:
            min_value_str = utcTolocaltime(min_value).strftime(datefmt)
        if max_value and type(max_value) is datetime:
            max_value_str = utcTolocaltime(max_value).strftime(datefmt)
        return shared.DateInput(
            input_name=input_name,
            min_value=min_value_str,
            max_value=max_value_str,
            value=value,
        )


class DateRangeFilterFactory:
    @classmethod
    def create(
        cls,
        form_method: str = templates_string.FormMethod.GET.value,
        form_action: str = "",
        title: str = "日付の範囲",
        submit_value: str = "抽出する",
        lower_name: str = FilterQueryName.MIN_DATE.value,
        lower_min: datetime | None = None,
        lower_max: datetime | None = None,
        lower_value: str = "",
        upper_name: str = FilterQueryName.MAX_DATE.value,
        upper_min: datetime | None = None,
        upper_max: datetime | None = None,
        upper_value: str = "",
    ) -> shared.RangeInputForm:
        return shared.RangeInputForm(
            form=shared.Form(action=form_action, method=form_method),
            range_input=shared.RangeInput(
                title=title,
                submit_value=submit_value,
                lower=DateInputFactory.create(
                    input_name=lower_name,
                    min_value=lower_min,
                    max_value=lower_max,
                    value=lower_value,
                ),
                upper=DateInputFactory.create(
                    input_name=upper_name,
                    min_value=upper_min,
                    max_value=upper_max,
                    value=upper_value,
                ),
            ),
        )

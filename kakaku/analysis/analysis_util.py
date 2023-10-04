from datetime import datetime
from dateutil.relativedelta import relativedelta

from common import (
    filter_name,
    util as cmn_util,
)

def get_days_of_AnalysisTermId(atid : int):
    if atid == filter_name.AnalysisTermName.ONE_WEEK.id:
        return 7
    if atid == filter_name.AnalysisTermName.TWO_WEEK.id:
        return 14
    
    now = cmn_util.utcTolocaltime(datetime.utcnow())
    if atid == filter_name.AnalysisTermName.ONE_MONTH.id:
        date = now + relativedelta(months=-1)
        delta = now - date
        return delta.days
    if atid == filter_name.AnalysisTermName.THREE_MONTH.id:
        date = now + relativedelta(months=-3)
        delta = now - date
        return delta.days
    if atid == filter_name.AnalysisTermName.SIX_MONTH.id:
        date = now + relativedelta(months=-6)
        delta = now - date
        return delta.days
    if atid == filter_name.AnalysisTermName.ONE_YEAR.id:
        date = now + relativedelta(years=-1)
        delta = now - date
        return delta.days
    
import os
from accessor.item import (
    UrlQuery,
)
from common import cmnlog

def updateAllitems(dlproc):
    logheader = os.path.basename(__file__)
    logger = cmnlog.getLogger(cmnlog.LogName.MANAGER)
    logger.info(logheader + ' get UPDATE_ACT_ALL')
    ret = UrlQuery.get_act_items_url()
    items = [dict(row._mapping.items()) for row in ret]
    logger.info('{} ACT ITEMS NUM={}'.format(logheader, len(items)))
    for item in items:
        dlproc.putDlTask(item['urlpath'], item['item_id'])
    logger.info(logheader + ' put end UPDATE_ACT_ALL')
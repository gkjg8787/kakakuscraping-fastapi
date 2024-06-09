import sys
import json
import requests
from requests.exceptions import Timeout, ConnectionError

from itemcomb.surugaya_postage.const_value import (
    SHIPPING_FEE_URL,
    DEFAULT_PREF,
)

REQUESTS_TIMEOUT = (3.5, 7.0)


def getRawShippingFee(tenpo_cd):
    payload = {"tenpo_cd": tenpo_cd}
    url = SHIPPING_FEE_URL
    try:
        res = requests.post(url=url, data=payload, timeout=REQUESTS_TIMEOUT)
    except Timeout:
        # print('Timeout Error')
        return None
    except ConnectionError:
        return None
    if res.status_code != requests.codes.ok:
        # print('Error Status Code' + str(res.status_code))
        return None
    res.encoding = res.apparent_encoding
    # charset = res.encoding
    return res.text


def has_list_pref_fee(jdict: dict):
    if "data" not in jdict:
        return False
    if "list_pref_fee" not in jdict["data"]:
        return False
    if jdict["data"]["list_pref_fee"]:
        return True
    return False


def searchPrefecturePostage(jdict: dict, prefecture=DEFAULT_PREF):
    if "data" not in jdict:
        # print('not exist key=data')
        return {}
    if "shipping" not in jdict["data"]:
        # print('not exist key=shipping')
        return {}
    sdict = jdict["data"]["shipping"]
    res = {
        "shipping_id": sdict["id"],
        "option": sdict["option"],
        "national_fee": sdict["national_fee"],
        "warning": "",
    }
    if not sdict["exception"] is None:
        res["exception"] = sdict["exception"]
        # print('exception='+sdict['exception'])
    if len(jdict["data"]["list_zip_national_fee"]) > 0:
        # print('list_zip_national_fee is exist')
        res["warning"] = "list_zip_national_fee is exist"
    if len(jdict["data"]["list_pref_fee"]) == 0:
        # print('list_pref_fee not exist')
        if len(res["warning"]) > 0:
            res["warning"] += ", "
        res["warning"] += "list_pref_fee not exist"
        # print(res)
        return res

    for pref in jdict["data"]["list_pref_fee"]:
        if prefecture == pref["prefecture"]:
            res.update(pref)
            break

    # print(res)
    return res


def getPrefecturePostage(tenpo_cd, prefs) -> None | list[dict]:
    jsontext = getRawShippingFee(tenpo_cd)
    if not jsontext:
        return None
    try:
        jdict = json.loads(jsontext)
    except json.decoder.JSONDecodeError:
        return None
    if has_list_pref_fee(jdict):
        return [searchPrefecturePostage(jdict, pref) for pref in prefs]
    else:
        return [searchPrefecturePostage(jdict)]

import sys
import json
import requests

from itemcomb.surugaya_postage.const_value import (
    SHIPPING_FEE_URL,
    DEFAULT_PREF,
)

def getRawShippingFee(tenpo_cd):
    payload = {'tenpo_cd':tenpo_cd }
    url = SHIPPING_FEE_URL
    res = requests.post(url=url, data=payload)
    if res.status_code != requests.codes.ok:
        print('Error Status Code' + str(res.status_code))
        return
    res.encoding = res.apparent_encoding
    #charset = res.encoding
    return res.text

def searchPrefecturePostage(jsontext, prefecture=DEFAULT_PREF):
    jdict = json.loads(jsontext)
    if not 'data' in jdict:
        print('not exist key=data')
        return {}
    if not 'shipping' in jdict['data']:
        print('not exist key=shipping')
        return {}
    sdict = jdict['data']['shipping']    
    res = {'shipping_id':sdict['id']
           , 'option':sdict['option']
           , 'national_fee':sdict['national_fee']
           , 'warning':''
           }
    if not sdict['exception'] is None:
        res['exception'] = sdict['exception']
        #print('exception='+sdict['exception'])
    if len(jdict['data']['list_zip_national_fee']) > 0:
        #print('list_zip_national_fee is exist')
        res['warning'] = 'list_zip_national_fee is exist'
    if len(jdict['data']['list_pref_fee']) == 0:
        #print('list_pref_fee not exist')
        if len(res['warning']) > 0:
            res['warning'] += ', '
        res['warning'] += 'list_pref_fee not exist'
        #print(res)
        return res

    for pref in jdict['data']['list_pref_fee']:
        if prefecture == pref['prefecture']:
            res.update(pref)
            break

    #print(res)
    return res


def getPrefecturePostage(tenpo_cd, prefs):
    jsontext = getRawShippingFee(tenpo_cd)
    jdicts = [searchPrefecturePostage(jsontext, pref) for pref in prefs]        
    return jdicts

def cmdstart():
    if len(sys.argv) == 1 or len(sys.argv) > 3:
        print('Error Param')
        return
    pref = DEFAULT_PREF
    if len(sys.argv) == 3:
        pref=sys.argv[2]
    jdicts = getPrefecturePostage(sys.argv[1], [pref])
    print(jdicts)


if __name__ == '__main__':
    cmdstart()


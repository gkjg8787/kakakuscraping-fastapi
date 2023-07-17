import os
from enum import Enum, auto
import argparse
from typing import List, Dict
from functools import wraps

from common import cmnlog, const_value
from accessor.item.item import OldItemQuery, OrganizerQuery
from accessor.server import OrganizeLogQuery
from model.item import PriceLog_2days, PriceLog


#古いDBへ移動する条件の経過日数
DAYS_TO_MOVE_OLD_DATA = 730

#pricelog_2daysがurl_id,storename毎に保持するデータ数の最大
MAX_LOG_2DAYS_DATA_CNT = 2

class DBOrganizerCmd(Enum):
    ALL = auto()
    PRICELOG_CLEANER = auto()
    PRICELOG_2DAYS_CLEANER = auto()
    SYNC_PRICELOG = auto()
    COMBINE_DUPLICATES = auto()

class FuncStatus(Enum):
    START = auto()
    END = auto()


def get_filename():
    return os.path.basename(__file__)

def getLogger():
    return cmnlog.getLogger(cmnlog.LogName.DB_ORGANIZE)

def output_func_db_log(name :DBOrganizerCmd, status :FuncStatus):
    OrganizeLogQuery.add_log(name=name.name, status=status.name)

def start_end_db_log(name):
    def _start_end_db_log(func) :
        @wraps(func)
        def wrapper(*args, **kargs) :
            output_func_db_log(name, FuncStatus.START)
            result = func(*args,**kargs)
            output_func_db_log(name, FuncStatus.END)
            return result
        return wrapper
    return _start_end_db_log

@start_end_db_log(DBOrganizerCmd.SYNC_PRICELOG)
def sync_2days_to_pricelog_today():
    today_2days_update_list = OrganizerQuery.get_pricelog_2days_today()
    log = getLogger()
    if len(today_2days_update_list) == 0:
        log.info(get_filename() + f" sync_2days_to_pricelog_today no update")
        return

    today_pricelog_list = OrganizerQuery.get_pricelog_today()
    if len(today_pricelog_list) == 0:
        add_dict_list :List[Dict] = []
        for p in today_2days_update_list:
            dic = p.toDict()
            dic.pop('log_id')
            add_dict_list.append(dic)
        log.info(get_filename() + f" sync_2days_to_pricelog_today add length={len(add_dict_list)}")
        #log.info(get_filename() + f"{add_dict_list}")
        log.info(get_filename() + f" sync_2days_to_pricelog_today add start")
        OrganizerQuery.add_price_log_by_dict_list(add_dict_list)
        log.info(get_filename() + f" sync_2days_to_pricelog_today add end")
        return
    
    results = __get_update_for_pricelog_by_2days(two_days_list=today_2days_update_list,
                                                        pricelog_list=today_pricelog_list)
    
    if len(results['update']) > 0:
        log.info(get_filename() + f" sync_2days_to_pricelog_today update length={len(results['update'])}")
        #log.info(get_filename() + f"{results['update']}")
        log.info(get_filename() + f" sync_2days_to_pricelog_today update start")
        OrganizerQuery.update_pricelog_by_dict_list(results['update'])
        log.info(get_filename() + f" sync_2days_to_pricelog_today update end")
    if len(results['add']) > 0:
        log.info(get_filename() + f" sync_2days_to_pricelog_today add length={len(results['add'])}")
        log.info(get_filename() + f" sync_2days_to_pricelog_today add start")
        #log.info(get_filename() + f"{results['add']}")
        OrganizerQuery.add_price_log_by_dict_list(results['add'])
        log.info(get_filename() + f" sync_2days_to_pricelog_today add end")
    return

def __get_update_for_pricelog_by_2days(two_days_list :List[PriceLog_2days],
                                       pricelog_list:List[PriceLog]):
    update_dict_list :List = []
    add_dict_list :List = []
    def is_update(two :PriceLog_2days, pricelog :PriceLog):
        if two.created_at < pricelog.created_at:
            return False
        if two.url_id != pricelog.url_id\
                or two.storename != pricelog.storename:
            return False
        if two.newprice == pricelog.newprice\
                and two.usedprice == pricelog.usedprice:
            return False
        return True
    def eq_log(two :PriceLog_2days, pricelog :PriceLog):
        return two.compare_self_to_pricelog(pricelog)
        
    for two in two_days_list:
        exist_log = False
        for pricelog in pricelog_list:
            if is_update(two=two, pricelog=pricelog):
                dic = two.toDict()
                dic['log_id'] = pricelog.log_id
                update_dict_list.append(dic)
                #print(f"two={two}, pricelog={pricelog}")
                continue
            if eq_log(two=two, pricelog=pricelog):
                exist_log = True
                continue
        if not exist_log:
            dic = two.toDict()
            dic.pop('log_id')
            add_dict_list.append(dic)

    return {'update':update_dict_list, 'add':add_dict_list}


@start_end_db_log(DBOrganizerCmd.PRICELOG_CLEANER)
def pricelog_cleaner():
    old_list = OrganizerQuery.get_old_pricelog_before_days(DAYS_TO_MOVE_OLD_DATA)
    move_list :List[Dict]= []
    for old in old_list:
        move_list.append(old.toDict())
    if len(move_list) > 0:
        log = getLogger()
        log.info(get_filename() + f" pricelog_cleaner move length={len(move_list)}")
        log.info(get_filename() + f" pricelog_cleaner move start")
        OldItemQuery.add_pricelog_of_old_by_dict_list(move_list)
        log.info(get_filename() + f" pricelog_cleaner move end")
    OrganizerQuery.delete_old_pricelog_before_days(DAYS_TO_MOVE_OLD_DATA)

@start_end_db_log(DBOrganizerCmd.PRICELOG_2DAYS_CLEANER)
def pricelog_2days_cleaner():
    OrganizerQuery.delete_old_pricelog_2days_before_days(DAYS_TO_MOVE_OLD_DATA)
    
    pricelog_result = OrganizerQuery.get_pricelog_2days_all()
    delete_pricelog_list = __get_delete_pricelog_2days_list(pricelog_result)
    #print(f"delete_list_len={len(delete_pricelog_list)}")
    if len(delete_pricelog_list) > 0:
        log = getLogger()
        log.info(get_filename() + f" pricelog_2days_cleaner delete length={len(delete_pricelog_list)}")
        delete_log_id_list = [v.log_id for v in delete_pricelog_list]
        log.info(get_filename() + f" pricelog_2days_cleaner delete start")
        OrganizerQuery.delete_pricelog_2days_by_log_id_list(delete_log_id_list)
        log.info(get_filename() + f" pricelog_2days_cleaner delete end")

def __get_delete_pricelog_2days_list(pricelog_result :List[PriceLog_2days]):
    pricelog_dict :Dict[str, List[PriceLog_2days]]= {}
    pricelog_data_cnt :Dict[str, int] = {}
    delete_pricelog_list :List[PriceLog_2days] = []
  
    for r in pricelog_result:
        key = str(r.url_id) + ":"+ r.storename
        if key in pricelog_dict:
            pricelog_dict[key].append(r)
        else:
            pricelog_dict[key] = [r]
        if key in pricelog_data_cnt:
            pricelog_data_cnt[key] += 1
            if pricelog_data_cnt[key] > MAX_LOG_2DAYS_DATA_CNT:
                old = __get_old_pricelog_2days(pricelog_dict[key])
                if old:
                    delete_pricelog_list.append(old)
                    pricelog_dict[key].remove(old)
                    pricelog_data_cnt[key] -= 1
            continue
        else:
            pricelog_data_cnt[key] = 1
            continue
    return delete_pricelog_list

def __get_old_pricelog_2days(pricelog_list :List[PriceLog_2days]):
    old = None
    for pricelog in pricelog_list:
        if not old:
            old = pricelog
            continue
        if old.created_at > pricelog.created_at:
            old = pricelog
    return old

@start_end_db_log(DBOrganizerCmd.COMBINE_DUPLICATES)
def pricelog_combine_duplicates():
    COMBINE_DAYS = 1 #同じstorenameのデータを結合する対象のログに相対日付
    for days in range(0, COMBINE_DAYS+1):
        __pricelog_combine_duplicates(days)
        __pricelog_2days_combine_duplicates(days)

def __pricelog_combine_duplicates(days :int):
    log = getLogger()
    log.info(get_filename() + f" pricelog_combine_duplicates target days=-{days}")
    results = OrganizerQuery.get_old_pricelog_by_days(days)
    log.info(get_filename() + f" pricelog_combine_duplicates original length={len(results)}")

    combine_list = __combine_duplicates_data(results)
    log.info(get_filename() + f" pricelog_combine_duplicates combine length={len(combine_list)}")

    delete_log_id_list = [v.log_id for v in results]
    log.info(get_filename() + f" pricelog_combine_duplicates delete start")
    OrganizerQuery.delete_pricelog_by_log_id_list(delete_log_id_list)
    log.info(get_filename() + f" pricelog_combine_duplicates delete end")

    log.info(get_filename() + f" pricelog_combine_duplicates add start")
    OrganizerQuery.add_price_log_by_dict_list([p.toDict() for p in combine_list])
    log.info(get_filename() + f" pricelog_combine_duplicates add end")

def __combine_duplicates_data(two_days_list :List[PriceLog]):
    results :List[PriceLog] = []
    dup_dict :Dict[str, List[PriceLog]] = {}
    def __get_key(p :PriceLog):
        return f"{p.url_id}:{p.storename}"
    for two in two_days_list:
        key = __get_key(two)
        if two.storename in dup_dict:
            dup_dict[key].append(two)
        else:
            dup_dict[key] = [two]

    def __is_combine_price(current :int, insert: int):
        if current == const_value.INIT_PRICE\
        and insert != const_value.INIT_PRICE:
            return True
        if current != const_value.INIT_PRICE\
        and insert != const_value.INIT_PRICE\
        and current > insert:
            return True
        return False
    
    for k,v in dup_dict.items():
        if len(v) == 1:
            results.append(v[0])
            continue
        if len(v) > 1:
            p = None
            for log in v:
                if p is None:
                    p = PriceLog()
                    p.url_id = log.url_id
                    p.created_at = log.created_at
                    p.uniqname = log.uniqname
                    p.usedprice = log.usedprice
                    p.newprice = log.newprice
                    p.taxin = log.taxin
                    p.onsale = log.onsale
                    p.salename = log.salename
                    p.issuccess = log.issuccess
                    p.trendrate = log.trendrate
                    p.storename = log.storename
                    continue
                else:
                    is_combine = False
                    if __is_combine_price(p.newprice, log.newprice):
                        is_combine = True
                        p.newprice = log.newprice
                    if __is_combine_price(p.usedprice, log.usedprice):
                        is_combine = True
                        p.usedprice = log.usedprice
                    if is_combine:
                        if p.trendrate > log.trendrate:
                            p.trendrate = log.trendrate
                            p.onsale = log.onsale
                            p.salename = log.salename
            results.append(p)
            continue
    return results

def __pricelog_2days_combine_duplicates(days :int):
    log = getLogger()
    log.info(get_filename() + f" pricelog_combine_duplicates target days=-{days}")
    results = OrganizerQuery.get_old_pricelog_2days_by_days(days)
    log.info(get_filename() + f" pricelog_combine_duplicates original length={len(results)}")

    combine_list = __combine_duplicates_data_2days(results)
    log.info(get_filename() + f" pricelog_combine_duplicates combine length={len(combine_list)}")

    delete_log_id_list = [v.log_id for v in results]
    log.info(get_filename() + f" pricelog_combine_duplicates delete start")
    OrganizerQuery.delete_pricelog_2days_by_log_id_list(delete_log_id_list)
    log.info(get_filename() + f" pricelog_combine_duplicates delete end")

    log.info(get_filename() + f" pricelog_combine_duplicates add start")
    OrganizerQuery.add_price_log_2days_by_dict_list([p.toDict() for p in combine_list])
    log.info(get_filename() + f" pricelog_combine_duplicates add end")

def __combine_duplicates_data_2days(two_days_list :List[PriceLog_2days]):
    results :List[PriceLog_2days] = []
    dup_dict :Dict[str, List[PriceLog_2days]] = {}
    def __get_key(p :PriceLog_2days):
        return f"{p.url_id}:{p.storename}"
    for two in two_days_list:
        key = __get_key(two)
        if two.storename in dup_dict:
            dup_dict[key].append(two)
        else:
            dup_dict[key] = [two]

    def __is_combine_price(current :int, insert: int):
        if current == const_value.INIT_PRICE\
        and insert != const_value.INIT_PRICE:
            return True
        if current != const_value.INIT_PRICE\
        and insert != const_value.INIT_PRICE\
        and current > insert:
            return True
        return False
    
    for k,v in dup_dict.items():
        if len(v) == 1:
            results.append(v[0])
            continue
        if len(v) > 1:
            p = None
            for log in v:
                if p is None:
                    p = PriceLog_2days()
                    p.url_id = log.url_id
                    p.created_at = log.created_at
                    p.uniqname = log.uniqname
                    p.usedprice = log.usedprice
                    p.newprice = log.newprice
                    p.taxin = log.taxin
                    p.onsale = log.onsale
                    p.salename = log.salename
                    p.issuccess = log.issuccess
                    p.trendrate = log.trendrate
                    p.storename = log.storename
                    continue
                else:
                    is_combine = False
                    if __is_combine_price(p.newprice, log.newprice):
                        is_combine = True
                        p.newprice = log.newprice
                    if __is_combine_price(p.usedprice, log.usedprice):
                        is_combine = True
                        p.usedprice = log.usedprice
                    if is_combine:
                        if p.trendrate > log.trendrate:
                            p.trendrate = log.trendrate
                            p.onsale = log.onsale
                            p.salename = log.salename
            results.append(p)
            continue
    return results

def param_parser(argv):
    parser = argparse.ArgumentParser(description='table organizer')
    cmd_list = [v.name.upper() for v in DBOrganizerCmd]
    cmd_list.extend([v.name.lower() for v in DBOrganizerCmd])
    parser.add_argument('name', type=str, choices=cmd_list)
    
    args = parser.parse_args(argv[1:])
    return args

def start_func(orgcmd :DBOrganizerCmd):
    if orgcmd == DBOrganizerCmd.ALL:
        pricelog_cleaner()
        sync_2days_to_pricelog_today()
        pricelog_2days_cleaner()
        return
    if orgcmd == DBOrganizerCmd.SYNC_PRICELOG:
        sync_2days_to_pricelog_today()
        return
    if orgcmd == DBOrganizerCmd.PRICELOG_2DAYS_CLEANER:
        pricelog_2days_cleaner()
        return
    if orgcmd == DBOrganizerCmd.PRICELOG_CLEANER:
        pricelog_cleaner()
        return
    if orgcmd == DBOrganizerCmd.COMBINE_DUPLICATES:
        pricelog_combine_duplicates()
        return
    return

def start_cmd(argv):
    param = param_parser(argv)
    if not param.name:
        print('No Param, Please cmd name')
        return
    cmnlog.createLogger(cmnlog.LogName.DB_ORGANIZE)
    for i in DBOrganizerCmd:
        if i.name.upper() == param.name.upper():
            print(f'start func {str(param.name).upper()}')
            start_func(i)
            print(f'end func {str(param.name).upper()}')
            break

from typing import Optional
from datetime import datetime

from enum import Enum

from distutils.util import strtobool
import statistics

from sqlalchemy.orm import Session

from pydantic import BaseModel

from accessor.item.item import AnalysisQuery
from accessor.item import UrlActive
from analysis import analysis_util
from accessor.util import sqlalchemy_result_all_to_dict_list

from common.const_value import INIT_PRICE
from common.util import utcTolocaltime

class AnalysisKeyName:
    PERIOD_DATETIME = "period_datetime"
    PERIOD_ITEMID = "period_itemid"
    PERIOD_URLID = "period_urlid"
    PERIOD_LOG = "period_log"
    ITEM_PRICE = "item_price"
    URL = "url"
    ERROR = "error"

    START = "start"
    END = "end"
    ACT = "act"
    INACT = "inact"
    COMMON = "common"

    INIT_PRICE = "init_price"
    AVERAGE = "average"
    MEDIAN = "median"
    PRICE = "price"
    UP = "up"
    DOWN = "down"
    NO_CHANGE = "no_change"
    TO_IN_STOCK = "to_in_stock"
    TO_OUT_OF_STOCK = "to_out_of_stock"
    NO_STOCK = "no_stock"

    SUCCESS = "success"
    FAILED = "failed"
    STORE = "store"

    STORE_PER_URL = "store_per_url"

class LogAnalysisError(Enum):
    DATA_IS_ZERO = "分析対象のログが存在しません"
    DICT_IS_ZERO = "分析対象のログが存在しません"
    NO_EXIST_DATETIME = "対象期間のログが取得できません"
    NOT_ENOUGH_LOGS = "分析に必要である十分なログがありません"

def get_log_analysis(db :Session, atid :int):
    days = analysis_util.get_days_of_AnalysisTermId(atid)
    r = AnalysisQuery.get_itemlog_period_datetime_from_day(db, days=-days)
    rd_list = sqlalchemy_result_all_to_dict_list(r)
    error_dict = {}
    if len(rd_list) == 0\
        or len(rd_list[0]) == 0\
        or not rd_list[0][AnalysisKeyName.START]\
            and not rd_list[0][AnalysisKeyName.END]:
        error_dict[AnalysisKeyName.ERROR] = LogAnalysisError.DICT_IS_ZERO
        return LogAnalysisResult(error_dict)
    if not_exist_datetime_in_dict(rd_list[0]):
        error_dict[AnalysisKeyName.ERROR] = LogAnalysisError.NO_EXIST_DATETIME
        return LogAnalysisResult(error_dict)
    
    period_start_jst = utcTolocaltime(rd_list[0][AnalysisKeyName.START])
    period_end_jst = utcTolocaltime(rd_list[0][AnalysisKeyName.END])
    if period_start_jst.date() == period_end_jst.date():
        error_dict[AnalysisKeyName.ERROR] = LogAnalysisError.NOT_ENOUGH_LOGS
        return LogAnalysisResult(error_dict)
    
    result = AnalysisQuery.get_itemlog_by_period_date(db,
                                                      start_jst=period_start_jst.date(),
                                                      end_jst=period_end_jst.date()
                                                      )
    logana = LogAnalysis(result)
    return logana.get_analysis_data()

def not_exist_datetime_in_dict(dic : dict):
    if not AnalysisKeyName.START in dic\
            or not AnalysisKeyName.END in dic:
        return True
    if AnalysisKeyName.START in dic\
        and not dic[AnalysisKeyName.START]:
        return True
    if AnalysisKeyName.END in dic\
        and not dic[AnalysisKeyName.END]:
        return True
    return False


def is_init_price(val :int):
    return val == INIT_PRICE

def get_lowest_price(a :int , b :int):
    if is_init_price(a):
        return b
    if is_init_price(b):
        return a
    if a > b:
        return b
    return a




class CountTrend(BaseModel):
    name :str
    is_up :bool = False
    is_down :bool = False
    value :int = 0

    def __init__(self, start :float, end :float):
        value = start - end
        if value > 0:
            super().__init__(name="減少", value=-1, is_down=True)
        elif value < 0:
            super().__init__(name="増加", value=1, is_up=True)
        else:
            super().__init__(name="変化なし")

class PriceTrend(BaseModel):
    name :str
    is_up :bool = False
    is_down :bool = False
    value :int = 0

    def __init__(self, start :float, end :float):
        value = start - end
        if value > 0:
            super().__init__(name="下落", value=-1, is_down=True)
        elif value < 0:
            super().__init__(name="上昇", value=1, is_up=True)
        else:
            super().__init__(name="変化なし")

class MultiPriceTrend(BaseModel):
    name :str
    is_up :bool = False
    is_down :bool = False
    value :int = 0

    def __init__(self,
                 up_count :int,
                 down_count :int,
                 start_average :float,
                 end_average :float,
                 ):
        trend = ""
        is_up = False
        is_down = False
        value = 0
        ct = PriceTrend(end=up_count, start=down_count)
        pt = PriceTrend(start=start_average, end=end_average)
        if ct.is_down and pt.is_down:
            trend = "下落"
            is_down = True
            value = -1
        elif ct.is_up and pt.is_up:
            trend = "上昇"
            is_up = True
            value = 1
        elif ct.value == 0 and pt.value == 0:
            trend = "変化なし"
        else:
            all_count = up_count + down_count
            sum_average = start_average + end_average
            up_rate = up_count / all_count
            down_rate = down_count / all_count
            start_rate = start_average / sum_average
            end_rate = end_average / sum_average
            max_rate = max([up_rate, down_rate, start_rate, end_rate])
            if max_rate == up_rate\
                or max_rate == start_rate:
                trend = "上昇"
                is_up = True
                value = 1
            elif max_rate == down_rate\
                or max_rate == end_rate:
                trend = "下落"
                is_down = True
                value = -1

        super().__init__(name=trend, is_up=is_up, is_down=is_down, value=value)

class CountResult(BaseModel):
    trend :CountTrend
    start :int = 0
    end :int = 0

    def __init__(self, start :int, end :int):
        trend = CountTrend(start, end)
        super().__init__(trend=trend, start=start, end=end)


class PriceResult(BaseModel):
    count :int = 0
    count_rate :float = 0.0
    average :float = 0.0

    def __init__(self, all_count :int, count :int, average :float):
        count_rate :float = float(count) / float(all_count)
        super().__init__(count=count, count_rate=count_rate, average=average)

class ItemPricePeriodResult(BaseModel):
    average :float = 0.0
    median :float = 0.0

class ItemPriceResult(BaseModel):
    updown_trend :MultiPriceTrend = None
    up :PriceResult = None
    down :PriceResult = None
    no_change :PriceResult = None

    average_trend :PriceTrend = None
    start :ItemPricePeriodResult = None
    end :ItemPricePeriodResult = None

    median_trend :PriceTrend = None

    to_in_stock :PriceResult = None
    to_out_of_stock :PriceResult = None
    no_stock :PriceResult = None

    def __init__(self,
                 up_dict :dict,
                 down_dict :dict,
                 no_change_count :int,
                 start_average :float,
                 end_average :float,
                 start_median :float,
                 end_median :float,
                 to_in_stock_count :int,
                 to_out_of_stock_count :int,
                 no_stock_count :int,
                 ):
        up_count = len(up_dict.keys())
        down_count = len(down_dict.keys())
        all_count = sum(
            [up_count, down_count, no_change_count,
             to_in_stock_count, to_out_of_stock_count, no_stock_count]
            )
        up_average = self.create_price_average(up_dict)
        up = PriceResult(all_count=all_count, count=up_count, average=up_average)
        down_average = self.create_price_average(down_dict)
        down = PriceResult(all_count=all_count, count=down_count, average=down_average)
        no_change = PriceResult(all_count=all_count, count=no_change_count, average=0)
        to_in_stock = PriceResult(all_count=all_count, count=to_in_stock_count, average=0)
        to_out_of_stock = PriceResult(all_count=all_count, count=to_out_of_stock_count, average=0)
        no_stock = PriceResult(all_count=all_count, count=no_stock_count, average=0)

        super().__init__(updown_trend=MultiPriceTrend(up_count, down_count, up_average, down_average),
                         up=up,
                         down=down,
                         no_change=no_change,
                         average_trend=PriceTrend(start_average, end_average),
                         start=ItemPricePeriodResult(average=start_average, median=start_median),
                         end=ItemPricePeriodResult(average=end_average, median=end_median),
                         median_trend=PriceTrend(start_median, end_median),
                         to_in_stock=to_in_stock,
                         to_out_of_stock=to_out_of_stock,
                         no_stock=no_stock,
                         )

    
    def create_price_average(self, price_dict :dict):
        if len(price_dict) == 0:
            return 0
        return statistics.mean(list(price_dict.values()))
    

class DownloadCountResult(BaseModel):
    success :int = 0
    failed :int = 0

class UrlDownLoadResult(BaseModel):
    trend :CountTrend
    start :DownloadCountResult
    end :DownloadCountResult

    def __init__(self,
                 start_success :int,
                 start_failed :int,
                 end_success :int,
                 end_failed :int,
                 ):
        start_all = start_success + start_failed
        end_all = end_success + end_failed
        start_suc_rate = start_success / start_all
        end_suc_rate = end_success / end_all
        super().__init__(trend=CountTrend(start_suc_rate, end_suc_rate),
                        start=DownloadCountResult(success=start_success, failed=start_failed),
                        end=DownloadCountResult(success=end_success, failed=end_failed),
                         )
    

class StoreMostCommonResult(BaseModel):
    start :list
    end :list

    def __init__(self, start_dict :dict, end_dict :dict, max_store_num :int = 0):
        if max_store_num < 0:
            max_store_num = 0

        start_l = sorted(start_dict.items(), key=lambda x:x[1], reverse=True)
        start = [{"storename":t[0], "count":t[1]} for t in start_l]

        end_l = sorted(end_dict.items(), key=lambda x:x[1], reverse=True)
        end = [{"storename":t[0], "count":t[1]} for t in end_l]
        if max_store_num > 0:
            if len(start) > max_store_num:
                start = start[:max_store_num]
            if len(end) > max_store_num:
                end = end[:max_store_num]
        super().__init__(start=start, end=end)
    
class UrlStoreCountAverageResult(BaseModel):
    trend :CountTrend
    start :float = 0
    end :float = 0

    def __init__(self, start_dict :dict, end_dict:dict):
        start_ave = self.create_average(start_dict)
        end_ave = self.create_average(end_dict)
        super().__init__(trend=CountTrend(start_ave, end_ave),
                         start=start_ave,
                         end=end_ave,
                         )
    
    def create_average(self, store_per_url :dict):
        all_store_count_list = [len(l) for l in store_per_url.values()]
        return statistics.mean(all_store_count_list)


class LogAnalysisResult:
    result :dict = {}
    def __init__(self, result :dict):
        self.result = result
    
    def get_dict(self):
        return self.result
    
    def is_error(self):
        return AnalysisKeyName.ERROR in self.result
    
    def get_error(self):
        return self.result[AnalysisKeyName.ERROR]
    
    def get_start_datetime(self) -> datetime:
        return self.result[AnalysisKeyName.PERIOD_DATETIME][AnalysisKeyName.START]
    
    def get_end_datetime(self) -> datetime:
        return self.result[AnalysisKeyName.PERIOD_DATETIME][AnalysisKeyName.END]
    
    def get_item_count(self) -> CountResult:
        start = len(self.get_start_itemid_act())
        end = len(self.get_end_itemid_act())
        return CountResult(start=start, end=end)

    def get_start_itemid_act(self) -> set:
        return self.result[AnalysisKeyName.PERIOD_ITEMID][AnalysisKeyName.START][AnalysisKeyName.ACT]
    
    def get_start_itemid_inact(self) -> set:
        return self.result[AnalysisKeyName.PERIOD_ITEMID][AnalysisKeyName.START][AnalysisKeyName.INACT]
    
    def get_end_itemid_act(self) -> set:
        return self.result[AnalysisKeyName.PERIOD_ITEMID][AnalysisKeyName.END][AnalysisKeyName.ACT]
    
    def get_end_itemid_inact(self) -> set:
        return self.result[AnalysisKeyName.PERIOD_ITEMID][AnalysisKeyName.END][AnalysisKeyName.INACT]

    def get_url_count(self) -> CountResult:
        start = len(self.get_start_urlid_act())
        end = len(self.get_end_urlid_act())
        return CountResult(start=start, end=end)
    
    def get_common_itemid_act(self) -> set:
        return self.result[AnalysisKeyName.PERIOD_ITEMID][AnalysisKeyName.COMMON][AnalysisKeyName.ACT]

    def get_start_urlid_act(self) -> set:
        return self.result[AnalysisKeyName.PERIOD_URLID][AnalysisKeyName.START][AnalysisKeyName.ACT]
    
    def get_start_urlid_inact(self) -> set:
        return self.result[AnalysisKeyName.PERIOD_URLID][AnalysisKeyName.START][AnalysisKeyName.INACT]
    
    def get_end_urlid_act(self) -> set:
        return self.result[AnalysisKeyName.PERIOD_URLID][AnalysisKeyName.END][AnalysisKeyName.ACT]
    
    def get_end_urlid_inact(self) -> set:
        return self.result[AnalysisKeyName.PERIOD_URLID][AnalysisKeyName.END][AnalysisKeyName.INACT]

    def get_common_urlid_act(self) -> set:
        return self.result[AnalysisKeyName.PERIOD_URLID][AnalysisKeyName.COMMON][AnalysisKeyName.ACT]

    def get_item_price(self) -> ItemPriceResult:
        return ItemPriceResult(up_dict=self.get_itemprice_up_dict(),
                               down_dict=self.get_itemprice_down_dict(),
                               no_change_count=len(self.get_itemprice_no_change_list()),
                               start_average=self.get_start_itemprice_average(),
                               end_average=self.get_end_itemprice_average(),
                               start_median=self.get_start_itemprice_median(),
                               end_median=self.get_end_itemprice_median(),
                               to_in_stock_count=len(self.get_itemprice_to_in_stock_list()),
                               to_out_of_stock_count=len(self.get_itemprice_to_out_of_stock_list()),
                               no_stock_count=len(self.get_itemprice_no_stock_list()),
                               )
    
    def get_start_itemprice_average(self) -> int:
        return int(self.result[AnalysisKeyName.ITEM_PRICE][AnalysisKeyName.START][AnalysisKeyName.AVERAGE])

    def get_end_itemprice_average(self) -> int:
        return int(self.result[AnalysisKeyName.ITEM_PRICE][AnalysisKeyName.END][AnalysisKeyName.AVERAGE])
    
    def get_start_itemprice_median(self) -> int:
        return int(self.result[AnalysisKeyName.ITEM_PRICE][AnalysisKeyName.START][AnalysisKeyName.MEDIAN])

    def get_end_itemprice_median(self) -> int:
        return int(self.result[AnalysisKeyName.ITEM_PRICE][AnalysisKeyName.END][AnalysisKeyName.MEDIAN])

    def get_start_itemprice_init_price_count(self) -> int:
        return len(self.result[AnalysisKeyName.ITEM_PRICE][AnalysisKeyName.START][AnalysisKeyName.INIT_PRICE])
    
    def get_end_itemprice_init_price_count(self) -> int:
        return len(self.result[AnalysisKeyName.ITEM_PRICE][AnalysisKeyName.END][AnalysisKeyName.INIT_PRICE])

    def get_itemprice_up_dict(self) -> dict:
        return self.result[AnalysisKeyName.ITEM_PRICE][AnalysisKeyName.PRICE][AnalysisKeyName.UP]
    
    def get_itemprice_down_dict(self) -> dict:
        return self.result[AnalysisKeyName.ITEM_PRICE][AnalysisKeyName.PRICE][AnalysisKeyName.DOWN]
    
    def get_itemprice_no_change_list(self) -> list:
        return list(self.result[AnalysisKeyName.ITEM_PRICE][AnalysisKeyName.PRICE][AnalysisKeyName.NO_CHANGE].keys())
    
    def get_itemprice_to_in_stock_list(self) -> list:
        return self.result[AnalysisKeyName.ITEM_PRICE][AnalysisKeyName.PRICE][AnalysisKeyName.TO_IN_STOCK]
    
    def get_itemprice_to_out_of_stock_list(self) -> list:
        return self.result[AnalysisKeyName.ITEM_PRICE][AnalysisKeyName.PRICE][AnalysisKeyName.TO_OUT_OF_STOCK]
    
    def get_itemprice_no_stock_list(self) -> list:
        return self.result[AnalysisKeyName.ITEM_PRICE][AnalysisKeyName.PRICE][AnalysisKeyName.NO_STOCK]
    
    def get_url_download(self) -> UrlDownLoadResult:
        return UrlDownLoadResult(start_success=len(self.get_start_url_success_list()),
                                 start_failed=len(self.get_start_url_failed_list()),
                                 end_success=len(self.get_end_url_success_list()),
                                 end_failed=len(self.get_end_url_failed_list()),
                                )

    def get_start_url_success_list(self) -> list:
        return list(self.result[AnalysisKeyName.URL][AnalysisKeyName.START][AnalysisKeyName.SUCCESS].keys())

    def get_start_url_failed_list(self) -> list:
        return list(self.result[AnalysisKeyName.URL][AnalysisKeyName.START][AnalysisKeyName.FAILED].keys())
    
    def get_end_url_success_list(self) -> list:
        return list(self.result[AnalysisKeyName.URL][AnalysisKeyName.END][AnalysisKeyName.SUCCESS].keys())

    def get_end_url_failed_list(self) -> list:
        return list(self.result[AnalysisKeyName.URL][AnalysisKeyName.END][AnalysisKeyName.FAILED].keys())
    
    def get_store_count(self) -> CountResult:
        return CountResult(start=len(self.get_start_store_dict().keys()),
                           end=len(self.get_end_store_dict()),
                           )

    def get_store_most_common(self, max_store_num :int = 0) -> StoreMostCommonResult:
        return StoreMostCommonResult(
            start_dict=self.get_start_store_dict(),
            end_dict=self.get_end_store_dict(),
            max_store_num=max_store_num,
        )

    def get_start_store_dict(self) -> dict:
        return self.result[AnalysisKeyName.URL][AnalysisKeyName.START][AnalysisKeyName.STORE]
    
    def get_end_store_dict(self) -> dict:
        return self.result[AnalysisKeyName.URL][AnalysisKeyName.END][AnalysisKeyName.STORE]
    
    def get_url_store_count_average(self) -> UrlStoreCountAverageResult:
        return UrlStoreCountAverageResult(
            start_dict=self.get_start_store_per_url_dict(),
            end_dict=self.get_end_store_per_url_dict(),
        )

    def get_start_store_per_url_dict(self) -> dict:
        return self.result[AnalysisKeyName.URL][AnalysisKeyName.START][AnalysisKeyName.STORE_PER_URL]
    
    def get_end_store_per_url_dict(self) -> dict:
        return self.result[AnalysisKeyName.URL][AnalysisKeyName.END][AnalysisKeyName.STORE_PER_URL]

class LogAnalysis:
    result :dict = {}
    

    def __init__(self, data):
        if len(data) == 0:
            self.result[AnalysisKeyName.ERROR] = LogAnalysisError.DATA_IS_ZERO
            return
        
        dict_list = sqlalchemy_result_all_to_dict_list(data)
        if len(dict_list) == 0:
            self.result[AnalysisKeyName.ERROR] = LogAnalysisError.DICT_IS_ZERO
            return
        
        start_datetime, end_datetime = self.get_period_end_datetime(dict_list=dict_list)
        if not start_datetime or not end_datetime:
            self.result[AnalysisKeyName.ERROR] = LogAnalysisError.NO_EXIST_DATETIME
            return
        
        if start_datetime == end_datetime:
            self.result[AnalysisKeyName.ERROR] = LogAnalysisError.NOT_ENOUGH_LOGS
            return

        convertdata :dict = {}
        convertdata[AnalysisKeyName.PERIOD_DATETIME] = {AnalysisKeyName.START : start_datetime,
                                             AnalysisKeyName.END : end_datetime,
                                             }
        convertdata.update(
            self.get_period_end_itemid_and_urlid(
                dict_list=dict_list,
                start_datetime=convertdata[AnalysisKeyName.PERIOD_DATETIME][AnalysisKeyName.START],
                end_datetime=convertdata[AnalysisKeyName.PERIOD_DATETIME][AnalysisKeyName.END],
            )
        )
        period_end_log = self.get_period_end_log(
            dict_list=dict_list,
            start_datetime=convertdata[AnalysisKeyName.PERIOD_DATETIME][AnalysisKeyName.START],
            end_datetime=convertdata[AnalysisKeyName.PERIOD_DATETIME][AnalysisKeyName.END],
        )
        item_price_analysis = self.get_item_price_analysis(
            common_ids=convertdata[AnalysisKeyName.PERIOD_ITEMID][AnalysisKeyName.COMMON][AnalysisKeyName.ACT],
            start_data=period_end_log[AnalysisKeyName.PERIOD_LOG][AnalysisKeyName.START],
            end_data=period_end_log[AnalysisKeyName.PERIOD_LOG][AnalysisKeyName.END],
        )
        url_analysis = self.get_url_analysis(
            common_ids=convertdata[AnalysisKeyName.PERIOD_URLID][AnalysisKeyName.COMMON][AnalysisKeyName.ACT],
            start_data=period_end_log[AnalysisKeyName.PERIOD_LOG][AnalysisKeyName.START],
            end_data=period_end_log[AnalysisKeyName.PERIOD_LOG][AnalysisKeyName.END],
        )

        self.result = {
            AnalysisKeyName.ITEM_PRICE : item_price_analysis,
            AnalysisKeyName.URL : url_analysis,
        }
        self.result.update(convertdata)
    
    def get_analysis_data(self):
        return LogAnalysisResult(self.result)
    
    @staticmethod
    def get_url_analysis(common_ids :list[int],
                         start_data :list[dict],
                         end_data :list[dict],
                        ):
        start_dayurl = DaysUrlLog(start_data)
        end_dayurl = DaysUrlLog(end_data)

        result = { AnalysisKeyName.START:{},
                   AnalysisKeyName.END:{}
                   }
        

        result[AnalysisKeyName.START][AnalysisKeyName.SUCCESS] = {}
        result[AnalysisKeyName.END][AnalysisKeyName.SUCCESS] = {}
        result[AnalysisKeyName.START][AnalysisKeyName.FAILED] = {}
        result[AnalysisKeyName.END][AnalysisKeyName.FAILED] = {}
        result[AnalysisKeyName.START][AnalysisKeyName.STORE] = {}
        result[AnalysisKeyName.END][AnalysisKeyName.STORE] = {}
        result[AnalysisKeyName.START][AnalysisKeyName.STORE_PER_URL] = {}
        result[AnalysisKeyName.END][AnalysisKeyName.STORE_PER_URL] = {}

        for id in common_ids:
            start_log_list = start_dayurl.get_url_log(id)
            end_log_list = end_dayurl.get_url_log(id)

            def analyse_url_log(log_list :list, key :str):
                for log in log_list:
                    if not id in result[key][AnalysisKeyName.SUCCESS]\
                        and not id in result[key][AnalysisKeyName.FAILED]:
                        if is_init_price(log["usedprice"])\
                            and is_init_price(log["newprice"]):
                            result[key][AnalysisKeyName.FAILED][id] = log["url_id"]
                        else:
                            result[key][AnalysisKeyName.SUCCESS][id] = log["url_id"]
                    
                    storename = log["storename"]
                    if storename\
                        and len(storename) > 0:
                        if storename in result[key][AnalysisKeyName.STORE]:
                            result[key][AnalysisKeyName.STORE][storename] += 1
                        else:
                            result[key][AnalysisKeyName.STORE][storename] = 1
                        
                        if not id in result[key][AnalysisKeyName.STORE_PER_URL]:
                            result[key][AnalysisKeyName.STORE_PER_URL][id] = set()
                        result[key][AnalysisKeyName.STORE_PER_URL][id].add(storename)
            
            analyse_url_log(start_log_list, AnalysisKeyName.START)
            analyse_url_log(end_log_list, AnalysisKeyName.END)

        return result
        
    @staticmethod
    def get_item_price_analysis(common_ids :list[int],
                                start_data :list[dict],
                                end_data :list[dict],
                                ):
        start_daysitem = DaysItemLog(start_data)
        end_daysitem = DaysItemLog(end_data)

        result = { AnalysisKeyName.START:{},
                   AnalysisKeyName.END:{}
                   }
        
        result[AnalysisKeyName.START][AnalysisKeyName.INIT_PRICE] = []
        result[AnalysisKeyName.END][AnalysisKeyName.INIT_PRICE] = []
        result[AnalysisKeyName.PRICE] = {}
        result[AnalysisKeyName.PRICE][AnalysisKeyName.UP] = {}
        result[AnalysisKeyName.PRICE][AnalysisKeyName.DOWN] = {}
        result[AnalysisKeyName.PRICE][AnalysisKeyName.NO_CHANGE] = {}
        result[AnalysisKeyName.PRICE][AnalysisKeyName.TO_IN_STOCK] = []
        result[AnalysisKeyName.PRICE][AnalysisKeyName.TO_OUT_OF_STOCK] = []
        result[AnalysisKeyName.PRICE][AnalysisKeyName.NO_STOCK] = []

        start_item_prices = {}
        end_item_prices = {}
        for id in common_ids:
            start_item_prices[id] = start_daysitem.get_lowest_price_in_item(id)
            end_item_prices[id] = end_daysitem.get_lowest_price_in_item(id)
            # -1 の数
            init_price_exist = False
            if is_init_price(start_item_prices[id]):
                result[AnalysisKeyName.START][AnalysisKeyName.INIT_PRICE].append(id)
                init_price_exist = True
            if is_init_price(end_item_prices[id]):
                result[AnalysisKeyName.END][AnalysisKeyName.INIT_PRICE].append(id)
                init_price_exist = True
            if init_price_exist:
                if is_init_price(start_item_prices[id])\
                    and not is_init_price(end_item_prices[id]):
                    result[AnalysisKeyName.PRICE][AnalysisKeyName.TO_IN_STOCK].append(id)
                elif not is_init_price(start_item_prices[id])\
                    and is_init_price(end_item_prices[id]):
                    result[AnalysisKeyName.PRICE][AnalysisKeyName.TO_OUT_OF_STOCK].append(id)
                else:
                    result[AnalysisKeyName.PRICE][AnalysisKeyName.NO_STOCK].append(id)
                continue
            # 値下がり価格　幅、数
            if start_item_prices[id] > end_item_prices[id]:
                val = start_item_prices[id] - end_item_prices[id]
                result[AnalysisKeyName.PRICE][AnalysisKeyName.DOWN][id] = val
                continue
            # 値上がり価格　幅、数
            if start_item_prices[id] < end_item_prices[id]:
                val = end_item_prices[id] - start_item_prices[id]
                result[AnalysisKeyName.PRICE][AnalysisKeyName.UP][id] = val
                continue
            # 変化なし　数
            if start_item_prices[id] == end_item_prices[id]:
                result[AnalysisKeyName.PRICE][AnalysisKeyName.NO_CHANGE][id] = 0
                continue

        result[AnalysisKeyName.START][AnalysisKeyName.AVERAGE] = statistics.mean(list(start_item_prices.values()))
        result[AnalysisKeyName.END][AnalysisKeyName.AVERAGE] = statistics.mean(list(end_item_prices.values()))
        result[AnalysisKeyName.START][AnalysisKeyName.MEDIAN] = statistics.median(list(start_item_prices.values()))
        result[AnalysisKeyName.END][AnalysisKeyName.MEDIAN] = statistics.median(list(end_item_prices.values()))

        return result
    
    @staticmethod
    def get_period_end_log(dict_list :list[dict],
                            start_datetime :datetime,
                            end_datetime :datetime):
        start_date = utcTolocaltime(start_datetime).date()
        end_date = utcTolocaltime(end_datetime).date()

        result = {
            AnalysisKeyName.PERIOD_LOG:{}
        }
        for dic in dict_list:
            if start_date == LogAnalysis.datetime_to_date(dic["created_at"]):
                if AnalysisKeyName.START in result[AnalysisKeyName.PERIOD_LOG]:
                    result[AnalysisKeyName.PERIOD_LOG][AnalysisKeyName.START].append(dic)
                else:
                    result[AnalysisKeyName.PERIOD_LOG][AnalysisKeyName.START] = [dic]
                continue
            if end_date == LogAnalysis.datetime_to_date(dic["created_at"]):
                if AnalysisKeyName.END in result[AnalysisKeyName.PERIOD_LOG]:
                    result[AnalysisKeyName.PERIOD_LOG][AnalysisKeyName.END].append(dic)
                else:
                    result[AnalysisKeyName.PERIOD_LOG][AnalysisKeyName.END] = [dic]
        return result
    
    @staticmethod
    def get_period_end_datetime(dict_list :list[dict]):
        min = None
        max = None
        for dic in dict_list:
            if not min\
                or min > dic["created_at"]:
                min = dic["created_at"]
            if not max\
                or max < dic["created_at"]:
                max = dic["created_at"]
        return min, max
    
    @staticmethod
    def datetime_to_date(val):
        return utcTolocaltime(val).date()

    @staticmethod
    def get_period_end_itemid_and_urlid(dict_list :list[dict],
                                        start_datetime :datetime,
                                        end_datetime :datetime):
        result = {}
        itemid_dic = IdAnalysisDict()
        urlid_dic = IdAnalysisDict()
        start_date = utcTolocaltime(start_datetime).date()
        end_date = utcTolocaltime(end_datetime).date()

        for dic in dict_list:
            if start_date == LogAnalysis.datetime_to_date(dic["created_at"]):
                if UrlActive.ACTIVE.value == dic["active"]:
                    itemid_dic.add_to_start(suf=AnalysisKeyName.ACT, val=dic["item_id"])
                    urlid_dic.add_to_start(suf=AnalysisKeyName.ACT, val=dic["url_id"])
                    continue
                if UrlActive.INACTIVE.value == dic["active"]:
                    itemid_dic.add_to_start(suf=AnalysisKeyName.INACT, val=dic["item_id"])
                    urlid_dic.add_to_start(suf=AnalysisKeyName.INACT, val=dic["url_id"])
                    continue
            if end_date == LogAnalysis.datetime_to_date(dic["created_at"]):
                if UrlActive.ACTIVE.value == dic["active"]:
                    itemid_dic.add_to_end(suf=AnalysisKeyName.ACT, val=dic["item_id"])
                    urlid_dic.add_to_end(suf=AnalysisKeyName.ACT, val=dic["url_id"])
                    continue
                if UrlActive.INACTIVE.value == dic["active"]:
                    itemid_dic.add_to_end(suf=AnalysisKeyName.INACT, val=dic["item_id"])
                    urlid_dic.add_to_end(suf=AnalysisKeyName.INACT, val=dic["url_id"])
                    continue
        itemid_dic.create_common()
        result[AnalysisKeyName.PERIOD_ITEMID] = {
            AnalysisKeyName.START : itemid_dic.start,
            AnalysisKeyName.END : itemid_dic.end,
            AnalysisKeyName.COMMON : itemid_dic.common,
        }
        urlid_dic.create_common()
        result[AnalysisKeyName.PERIOD_URLID] = {
            AnalysisKeyName.START : urlid_dic.start,
            AnalysisKeyName.END : urlid_dic.end,
            AnalysisKeyName.COMMON : urlid_dic.common,
        }
        return result


class IdAnalysisDict:
    start :dict[str, set[int]]
    end :dict[str, set[int]]
    common :dict[str, set[int]]

    def __init__(self):
        self.start = {
            AnalysisKeyName.ACT:set(),
            AnalysisKeyName.INACT:set(),
        }
        self.end = {
            AnalysisKeyName.ACT:set(),
            AnalysisKeyName.INACT:set(),
        }
        self.common = {
            AnalysisKeyName.ACT:set(),
        }
    def add_to_start(self, suf :str, val :int):
        self.start[suf].add(val)
    
    def add_to_end(self, suf :str, val :int):
        self.end[suf].add(val)
    
    def create_common(self):
        self.common[AnalysisKeyName.ACT] = set(
            self.get_common_ids(
                list(self.start[AnalysisKeyName.ACT]),
                list(self.end[AnalysisKeyName.ACT])
                )
            )

    def get_common_ids(self, a_list :list[int], b_list :list[int]):
        resultids :list = []
        for a in a_list:
            if a in b_list:
                resultids.append(a)
        return resultids


class DaysItemLog:
    item_log :dict[list]
    lowest_item_log :dict[dict]

    PRICE = "price"
    LOG = "log"

    def __init__(self, dict_list :list[dict]):
        self.item_log = self.create_item_log(dict_list)
        self.lowest_item_log = self.create_lowest_item_log(self.item_log)
    
    def get_item_log(self, item_id :int):
        return self.item_log[item_id]
    
    def get_lowest_price_in_item(self, item_id :int):
        return self.lowest_item_log[item_id][self.PRICE]

    def create_item_log(self, dict_list :list[dict]):
        result :dict[list] = {}
        for dic in dict_list:
            if dic["item_id"] in result:
                result[dic["item_id"]].append(dic)
            else:
                result[dic["item_id"]] = [dic]
        return result

    def create_lowest_item_log(self, result :dict):
        lowest_item_log = {}
        for key, item in result.items():
            low_price = None
            low_price_log = None
            for log in item:
                if is_init_price(log["usedprice"])\
                    and is_init_price(log["newprice"])\
                    and low_price_log:
                    continue
                if not low_price:
                    low_price = get_lowest_price(log["usedprice"], log["newprice"])
                    low_price_log = log                    
                    continue
                else:
                    cur_price = get_lowest_price(log["usedprice"], log["newprice"])
                    if cur_price < low_price:
                        low_price = cur_price
                        low_price_log = log
                    continue
            lowest_item_log[key] = {}
            lowest_item_log[key][self.PRICE] = low_price
            lowest_item_log[key][self.LOG] = low_price_log
        return lowest_item_log
    
class DaysUrlLog:
    url_log :dict[list] = {}

    def __init__(self, dict_list :list[dict]):
        self.url_log = self.create_url_log(dict_list)
    
    def get_url_log(self, url_id :int) -> list:
        return self.url_log[url_id]


    def create_url_log(self, dict_list :list[dict]):
        result :dict[list] = {}
        for dic in dict_list:
            if dic["url_id"] in result:
                result[dic["url_id"]].append(dic)
            else:
                result[dic["url_id"]] = [dic]
        return result

from datetime import datetime, timezone, timedelta
import copy

import pandas as pd
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from template_value import BaseTemplateValue
from template_value.storepostage import (
    StoreShippingTerms as SP_StoreShippingTerms,
    Terms as SP_Terms,
    BoundaryConverter,
)
from common import (
    filter_name,
    const_value,
    templates_string,
    util as cm_util,
    read_config,
)
from accessor.item import (
    NewestQuery,
    ItemQuery,
    UrlQuery,
    UrlActive,
    GroupQuery,
)
from accessor import store as ac_store
from analysis import database_analysis
from model import store as m_store
import parameter_parser.item as ppi
import parameter_parser.store as pps
from proc.scrapingmanage import sendTask
from proc.sendcmd import ScrOrder
from proc import get_sys_status, system_status
from proc import online_store_copy
from itemcomb.prefecture import PrefectureName
from url_search.surugaya import surugayaURL
from ml.predict_model import MinPriceModel, PredictionAccuracy
from proc.predict import MinPricePredict
from proc.predict.price_predict import (
    TargetColumnFeatureValueCreatorFactory,
    PriceLogChartPreProcessing,
)
from accessor.item.item import PredictionQuery
from accessor.util import get_dataframe_from_sql
from .shared import factory as shared_factory
from . import shared


def can_item_update(db: Session):
    syssts = get_sys_status.getSystemStatus(db)
    if (
        syssts == system_status.SystemStatus.FAULT.name
        or syssts == system_status.SystemStatus.STOP.name
        or syssts == system_status.SystemStatus.NONE.name
    ):
        return False
    return True


def get_gid_in_groups(gid: int, groups: list):
    for g in groups:
        if g.group_id == gid:
            return gid
    return filter_name.FilterDefault.GID


class NewestItemList(BaseTemplateValue):
    topscrollid: str
    res: list
    res_length: int = 0
    actstslist: list
    itemSortList: list
    groups: list
    storelist: list
    fquery: dict
    ZAIKO_CHECKED: str = ""
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value
    ITEMACT_NAME: str = filter_name.FilterQueryName.ACT.value
    ITEMSORT_NAME: str = filter_name.FilterQueryName.ISORT.value
    EQST_NAME: str = filter_name.FilterQueryName.STORE.value
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value
    POST_ITEM_ID: str = filter_name.TemplatePostName.ITEM_ID.value
    POST_GROUP_ID: str = filter_name.TemplatePostName.GROUP_ID.value
    POST_ITEM_ALL_UPDATE: str = filter_name.TemplatePostName.ITEM_ALL_UPDATE.value
    item_all_update_value: str = filter_name.ItemUpdateValue.ITEM_ALL_UPDATE
    POST_RETURN_USER: str = filter_name.TemplatePostName.RETURN_USER.value
    return_user: str = filter_name.FilterOnOff.ON
    STOCK_NAME: str = filter_name.FilterQueryName.ZAIKO.value
    STOCK_VALUE: int = filter_name.FilterOnOff.ON
    MIN_PRICE_RANGE_NAME: str = filter_name.FilterQueryName.PRMIN.value
    MAX_PRICE_RANGE_NAME: str = filter_name.FilterQueryName.PRMAX.value
    MIN_PRICE_RANGE: int | None = None
    MAX_PRICE_RANGE: int | None = None

    def __init__(self, nfq: ppi.NewestFilterQuery, db: Session):
        fd = nfq.get_filter_dict()
        super().__init__(
            topscrollid="",
            res=NewestQuery.get_newest_data(db, filter=fd),
            actstslist=ppi.get_actstslist(fd),
            itemSortList=ppi.get_item_sort_list(fd),
            groups=ppi.get_groups(db, f=fd),
            storelist=[],
            fquery=fd,
            ZAIKO_CHECKED=ppi.get_in_stock_filter_checked(fd),
        )

        self.res_length = len(self.res)
        self.storelist = pps.get_stores_for_newest(db, filter=self.fquery)

        if filter_name.FilterQueryName.GID.value in self.fquery:
            gid = int(self.fquery[filter_name.FilterQueryName.GID.value])
            self.fquery[filter_name.FilterQueryName.GID.value] = get_gid_in_groups(
                gid=gid, groups=self.groups
            )

        if filter_name.FilterQueryName.PRMIN.value in self.fquery:
            self.MIN_PRICE_RANGE = int(
                self.fquery[filter_name.FilterQueryName.PRMIN.value]
            )
        if filter_name.FilterQueryName.PRMAX.value in self.fquery:
            self.MAX_PRICE_RANGE = int(
                self.fquery[filter_name.FilterQueryName.PRMAX.value]
            )


class UpdateAllItemUrlPostContext(BaseTemplateValue):
    updateSuccess: bool = False
    return_user: bool = True
    errmsg: str = ""

    def __init__(self, db: Session):
        super().__init__()
        if not can_item_update(db):
            self.errmsg = "更新できない状態です。サーバを確認して下さい。"
            return
        self.update_all_data()

    def update_all_data(self):
        sendTask(ScrOrder.UPDATE_ACT_ALL, "", "")
        self.updateSuccess = True


class IdTextSelected(BaseModel):
    id: int
    selected: str = ""
    text: str


class ItemUrl(BaseModel):
    url_id: int
    item_url: str
    act_status: str

    def update(self, itemurl: type["ItemUrl"]):
        self.item_url = itemurl.item_url
        self.act_status = itemurl.act_status


class ItemPurchaseUrl(BaseModel):
    itemurls: list[ItemUrl]
    purchase_url: str
    itemurls_num: int = 0

    def __init__(self, itemurls: list[ItemUrl], purchase_url: str):
        super().__init__(itemurls=itemurls, purchase_url=purchase_url)
        self.itemurls_num = len(itemurls)

    def update(self, itemurl: ItemUrl):
        ret = self.get_itemurl(itemurl.url_id)
        if ret:
            ret.update(itemurl)
            return
        self.itemurls.append(itemurl)
        self.itemurls_num = len(self.itemurls)

    def get_itemurl(self, url_id: int):
        for itemurl in self.itemurls:
            if url_id == itemurl.url_id:
                return itemurl
        return None


class ItemDetailContext(BaseTemplateValue):
    loglist: list
    loglist_length: int = 0
    items: dict
    urllist: list
    purchase_urllist: list[ItemPurchaseUrl]
    timePeriodList: list[IdTextSelected]
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value
    TIME_PERIOD_Q_NAME: str = filter_name.ItemDetailQueryName.PERIODID.value
    POST_ITEM_ID: str = filter_name.TemplatePostName.ITEM_ID.value
    POST_URL_ID: str = filter_name.TemplatePostName.URL_ID.value
    POST_URL_PATH: str = filter_name.TemplatePostName.URL_PATH.value
    ACTIVE_VALUE: str = UrlActive.ACTIVE.value
    SEARCH_WORD_NAME: str = filter_name.FilterQueryName.WORD.value
    fquery: dict
    storelist: list
    EQST_NAME: str = filter_name.FilterQueryName.STORE.value
    COMPRESS_NAME: str = filter_name.FilterQueryName.PRESS.value
    COMPRESS_VALUE: int = filter_name.FilterOnOff.ON
    COMPRESS_CHECKED: str = ""
    item_created_at: datetime | None = None

    def __init__(self, db: Session, idq: ppi.ItemDetailQuery):
        fq = idq.get_filter_dict()
        super().__init__(
            loglist=[],
            items={},
            urllist=[],
            purchase_urllist=[],
            timePeriodList=[],
            fquery=fq,
            storelist=[],
            COMPRESS_CHECKED=ppi.get_compress_filter_checked(fq),
        )
        if not idq.itemid:
            return
        itemid = int(idq.itemid)
        periodid = filter_name.ItemDetailTimePeriodName.ONE_DAY.id
        if idq.periodid:
            periodid = int(idq.periodid)
        self.items = NewestQuery.get_newest_data_by_item_id(db, item_id=itemid)
        if not self.items:
            return

        item = ItemQuery.get_item(db=db, item_id=itemid)
        self.item_created_at = cm_util.utcTolocaltime(item.created_at)

        day = self.get_days_of_timeperiod(tpid=periodid)
        self.loglist = ItemQuery.get_item_pricelog_by_item_id_1year(
            db,
            item_id=itemid,
            result_limit=None,
            days=-day,
            storename=self.get_storename_by_store_id(db=db, store_id=idq.store),
        )
        if self.loglist:
            self.loglist = self.compress_logs(
                loglist=self.loglist, checked=self.COMPRESS_CHECKED
            )
            self.loglist_length = len(self.loglist)
            self.storelist = pps.get_stores_for_item_detail(
                db=db,
                filter=self.fquery,
                storename_list=ItemQuery.get_storename_by_item_id_1year(
                    db=db, item_id=itemid, days=-day
                ),
            )
        self.urllist = UrlQuery.get_urlinfo_by_item_id(db, item_id=itemid)
        if self.urllist:
            self.purchase_urllist = self.create_purchase_urllist(
                urllist=self.urllist, itemname=dict(self.items._mapping.items())["name"]
            )
        self.timePeriodList = self.create_time_period_list(periodid=periodid)

    def has_data(self) -> bool:
        if not self.items or len(self.items) == 0:
            return False
        return True

    def get_storename_by_store_id(self, db: Session, store_id: any) -> str:
        if not store_id:
            return ""
        if type(store_id) is str:
            if not str(store_id).isdigit() or int(store_id) <= 0:
                return ""
            store_id = int(store_id)
        storename = ac_store.StoreQuery.get_storename_by_store_id(
            db=db, store_id=store_id
        )
        if not storename:
            return ""
        return storename

    @staticmethod
    def create_time_period_list(periodid: int):
        timePeriodList = []
        for idtp in filter_name.ItemDetailTimePeriodName:
            iap = IdTextSelected(id=idtp.id, text=idtp.jname)
            if periodid == idtp.id:
                iap.selected = templates_string.HTMLOption.SELECTED.value
            timePeriodList.append(iap)
        return timePeriodList

    @staticmethod
    def get_days_of_timeperiod(tpid: int):
        if tpid == filter_name.ItemDetailTimePeriodName.ONE_DAY.id:
            return 1
        if tpid == filter_name.ItemDetailTimePeriodName.THREE_DAY.id:
            return 3
        if tpid == filter_name.ItemDetailTimePeriodName.ONE_WEEK.id:
            return 7
        if tpid == filter_name.ItemDetailTimePeriodName.TWO_WEEK.id:
            return 14

        now = cm_util.utcTolocaltime(datetime.now(timezone.utc))
        if tpid == filter_name.ItemDetailTimePeriodName.ONE_MONTH.id:
            date = now + relativedelta(months=-1)
            delta = now - date
            return delta.days
        if tpid == filter_name.ItemDetailTimePeriodName.THREE_MONTH.id:
            date = now + relativedelta(months=-3)
            delta = now - date
            return delta.days
        if tpid == filter_name.ItemDetailTimePeriodName.SIX_MONTH.id:
            date = now + relativedelta(months=-6)
            delta = now - date
            return delta.days
        if tpid == filter_name.ItemDetailTimePeriodName.ONE_YEAR.id:
            date = now + relativedelta(years=-1)
            delta = now - date
            return delta.days
        return 1

    def create_purchase_urllist(self, urllist: list, itemname: str):
        results: dict[str, ItemPurchaseUrl] = {}
        for url in urllist:
            d = dict(url._mapping.items())
            itemurl = ItemUrl(
                url_id=d["url_id"],
                item_url=d["urlpath"],
                act_status=d["active"],
            )
            purchase_url = surugayaURL.SurugayaPurchaseURL.get_url(
                urlpath=d["urlpath"], search_word=itemname
            )
            if purchase_url in results:
                results[purchase_url].update(itemurl)
                continue
            ipu = ItemPurchaseUrl(
                itemurls=[itemurl],
                purchase_url=purchase_url,
            )
            results[purchase_url] = ipu
        return list(results.values())

    def compress_logs(self, loglist: list, checked: str):
        if not checked:
            return loglist
        compresslog = CompressLogByStorename(
            loglist=[dict(row._mapping.items()) for row in loglist]
        )
        return compresslog.get_log_list()


class CompressLogByStorename:
    loglist: list[dict]

    def __init__(self, loglist: list[dict]):
        storename_to_list: dict[str, list] = {}
        for log in loglist:
            if log["storename"] in storename_to_list:
                storename_to_list[log["storename"]].append(log)
            else:
                storename_to_list[log["storename"]] = [log]
        results: list[dict] = []
        for dlist in storename_to_list.values():
            urlid_to_predata: dict[int, dict] = {}
            for d in sorted(dlist, key=lambda d: d["created_at"], reverse=True):
                urlid = int(d["url_id"])
                if urlid not in urlid_to_predata or not urlid_to_predata[urlid]:
                    urlid_to_predata[urlid] = d
                elif (
                    urlid == int(d["url_id"])
                    and urlid_to_predata[urlid]["usedprice"] == d["usedprice"]
                    and urlid_to_predata[urlid]["newprice"] == d["newprice"]
                ):
                    continue
                else:
                    urlid_to_predata[urlid] = d
                results.append(d)
        self.loglist = sorted(results, key=lambda r: r["created_at"], reverse=True)

    def get_log_list(self):
        return self.loglist


class ItemChartData(BaseModel):
    url_id: int = const_value.NONE_ID
    label: str = ""
    points: list = Field(default_factory=list)


class ItemDetailChartContext(BaseTemplateValue):
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value
    PERIOD_NAME: str = filter_name.FilterQueryName.PERIOD.value
    START_NAME: str = filter_name.FilterQueryName.START.value
    EACH_URL_NAME: str = filter_name.FilterQueryName.EACH.value
    PERIOD_MIN: int = 0
    PERIOD_MAX: int = 365
    chart_data: list
    item_id: int = const_value.NONE_ID
    item_name: str = ""
    fquery: dict
    date_range_filter: shared.RangeInputForm
    predict_length: int
    is_predict: bool = False
    has_multi_url: bool = False
    each_url_checked: str = ""
    result_msg_list: list[str]

    def __init__(self, idcq: ppi.ItemDetailChartQuery, db: Session):
        predict_conf = read_config.get_prediction_setting()
        if predict_conf.view:
            is_predict = True
            predict_length = None
            if idcq.period:
                predict_length = int(idcq.period)
            if not predict_length:
                predict_length = predict_conf.forecast_length
        else:
            is_predict = False
            predict_length = 0

        today = datetime.now(timezone.utc)
        today_jst = cm_util.utcTolocaltime(today)
        two_year_ago = today_jst - timedelta(days=365 * 2)

        super().__init__(
            chart_data=[],
            fquery=idcq.get_filter_dict(),
            date_range_filter=shared_factory.DateRangeFilterFactory.create(
                title="学習データの期間",
                lower_value=idcq.min_date,
                upper_value=idcq.max_date,
                lower_max=today_jst,
                upper_max=today_jst,
                lower_min=two_year_ago,
                upper_min=two_year_ago,
            ),
            predict_length=predict_length,
            is_predict=is_predict,
            result_msg_list=[],
        )
        if not idcq.itemid:
            return
        self.item_id = int(idcq.itemid)
        item = ItemQuery.get_item(db=db, item_id=self.item_id)
        self.item_name = item.name

        if idcq.each:
            self.each_url_checked = templates_string.HTMLOption.CHECKED.value

        start_date, end_date = self.get_default_chart_start_end_datetime()
        param_start_date, param_end_date = self.get_start_end_datetime(idcq=idcq)
        if start_date > param_start_date:
            start_date = param_start_date

        raw_df = get_dataframe_from_sql(
            stmt=PredictionQuery.get_stmt_pricelog_by_item_id_and_date_range(
                item_id=self.item_id, start=start_date, end=end_date
            )
        )
        url_df = raw_df["url_id"].unique()
        if len(url_df) > 1:
            self.has_multi_url = True

        if self.each_url_checked:
            df_list_dict = {}
            for url_id in url_df:
                df_list_dict[url_id] = raw_df.loc[(raw_df["url_id"] == url_id)]
        else:
            df_list_dict = {const_value.NONE_ID: raw_df}

        self.chart_data, errmsgs, accmsgs = self.create_chart_data(
            df_list_dict=df_list_dict,
            is_predict=self.is_predict,
            everytime_predict=predict_conf.everytime,
            start_predict=idcq.start,
            predict_length=predict_length,
            param_start_date=param_start_date,
            param_end_date=param_end_date,
            show_accuracy=predict_conf.show_accuracy,
            learning_timeout=predict_conf.learning_timeout,
        )
        if errmsgs:
            for errmsg in errmsgs:
                msg = errmsg["errmsg"]
                if errmsg["url_id"] and int(errmsg["url_id"]) > const_value.INIT_PRICE:
                    msg = f'url_id:{errmsg["url_id"]} {msg}'
                self.result_msg_list.append(msg)

        if accmsgs:
            for accmsg in accmsgs:
                msg = f'r2={accmsg["acc"].r2}'
                if accmsg["url_id"] and int(accmsg["url_id"]) > const_value.INIT_PRICE:
                    msg = f'url_id:{accmsg["url_id"]} {msg}'
                self.result_msg_list.append(msg)

    def has_data(self):
        if self.item_id == const_value.NONE_ID:
            return False
        if len(self.chart_data) == 0:
            return False
        return True

    @classmethod
    def create_itemchartdata(cls, url_id: int, label: str, data: list):
        if url_id != const_value.NONE_ID:
            label = f"{label}(url_id:{url_id})"
        return ItemChartData(url_id=url_id, label=label, points=data)

    @classmethod
    def get_point_data_and_msg(
        cls,
        url_id: int,
        df: pd.DataFrame,
        is_predict: bool,
        everytime_predict: bool,
        start_predict: str,
        predict_length: int,
        param_start_date: datetime,
        param_end_date: datetime | None,
        show_accuracy: bool,
        learning_timeout: int,
    ):
        results = []
        errmsgs = []
        accmsgs = []

        point_data_dict = cls._get_pricelist_of_uniq_point_data_for_df(df=df)
        used_list = point_data_dict["used"]
        results.append(
            cls.create_itemchartdata(url_id=url_id, label="中古価格", data=used_list)
        )
        new_list = point_data_dict["new"]
        results.append(
            cls.create_itemchartdata(url_id=url_id, label="新品価格", data=new_list)
        )

        if not is_predict:
            return results, errmsgs, accmsgs
        if not everytime_predict and not start_predict:
            return results, errmsgs, accmsgs
        predict_result = cls.get_predict_result(
            df=df,
            predict_length=predict_length,
            start=param_start_date,
            end=param_end_date,
            learning_timeout=learning_timeout,
        )
        if predict_result.errmsg:
            errmsgs.append({"url_id": url_id, "errmsg": predict_result.errmsg})
        used_predict = cls.get_used_predict_point_data(predict_result=predict_result)
        results.append(
            cls.create_itemchartdata(
                url_id=url_id, label="中古予想価格", data=used_predict
            )
        )
        if show_accuracy and predict_result.predict:
            acc = cls.get_accuracy(
                used_df=point_data_dict["used_df"],
                predict=predict_result.predict.predict,
                end=param_end_date,
            )
            if acc:
                accmsgs.append({"url_id": url_id, "acc": acc})
        return results, errmsgs, accmsgs

    @classmethod
    def create_chart_data(
        cls,
        df_list_dict: dict[list],
        is_predict: bool,
        everytime_predict: bool,
        start_predict: str,
        predict_length: int,
        param_start_date: datetime,
        param_end_date: datetime | None,
        show_accuracy: bool,
        learning_timeout: int,
    ):

        results = []
        errmsgs = []
        accmsgs = []
        for url_id, df in df_list_dict.items():
            res, err, acc = cls.get_point_data_and_msg(
                url_id=url_id,
                df=df,
                is_predict=is_predict,
                everytime_predict=everytime_predict,
                start_predict=start_predict,
                predict_length=predict_length,
                param_start_date=param_start_date,
                param_end_date=param_end_date,
                show_accuracy=show_accuracy,
                learning_timeout=learning_timeout,
            )
            if res:
                results.extend(res)
            if err:
                errmsgs.extend(err)
            if acc:
                accmsgs.extend(acc)
        return results, errmsgs, accmsgs

    @classmethod
    def get_default_chart_start_end_datetime(cls):
        now = datetime.now(timezone.utc)
        now = cm_util.utcTolocaltime(now).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start = now - timedelta(days=365)
        return start, None

    @staticmethod
    def str_to_datetime(value, tzinfo=None):
        date_fmt = "%Y-%m-%d"
        ret = datetime.strptime(value, date_fmt)
        if not tzinfo:
            return ret
        return ret.replace(tzinfo=tzinfo)

    @classmethod
    def get_start_end_datetime(cls, idcq: ppi.ItemDetailChartQuery):
        start = None
        if idcq.min_date:
            start = cls.str_to_datetime(idcq.min_date, tzinfo=cm_util.JST)
        end = None
        if idcq.max_date:
            end = cls.str_to_datetime(idcq.max_date, tzinfo=cm_util.JST)
        if not start:
            now = datetime.now(timezone.utc)
            now = cm_util.utcTolocaltime(now).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            start = now - timedelta(days=365)
        return start, end

    @classmethod
    def get_predict_result(
        cls,
        df: pd.DataFrame,
        predict_length: int,
        learning_timeout: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ):
        mpp = MinPricePredict(
            ml_model_class=MinPriceModel,
            fvcreator_factory_class=TargetColumnFeatureValueCreatorFactory,
        )

        result = mpp.get_predict(
            df=df,
            start=start,
            end=end,
            predict_length=predict_length,
        )
        return result

    @classmethod
    def get_used_predict_point_data(cls, predict_result):
        if predict_result.predict is None:
            return []
        if isinstance(predict_result.predict.index, pd.DatetimeIndex):
            x_list = predict_result.predict.index.strftime("%Y-%m-%d").tolist()
            y_list = list(predict_result.predict.predict)
            return [{"x": x, "y": round(y)} for x, y in zip(x_list, y_list)]
        else:
            x_list = predict_result.predict.index
            y_list = predict_result.predict.predict
            return [{"x": x, "y": round(y)} for x, y in zip(x_list, y_list)]

    @classmethod
    def get_accuracy(
        cls,
        used_df: pd.DataFrame,
        predict,
        end: datetime | None = None,
    ):
        if not end or len(used_df) == 0 or predict is None:
            return None
        df = used_df.copy()
        df["datetime"] = pd.to_datetime(df.index)
        used_min = "used_min"

        d_diff = df["datetime"].iloc[-1] - end.replace(tzinfo=None)
        if d_diff.days <= 1 or len(predict) == 1:
            return None
        if d_diff.days == len(predict):
            acc = PredictionAccuracy(
                actual=df[used_min].iloc[-len(predict) :], predict=predict
            )
        elif d_diff.days > len(predict):
            start_len = len(df) - d_diff.days
            if start_len < 0:
                return None
            acc = PredictionAccuracy(
                actual=df[used_min].iloc[start_len : start_len + len(predict)],
                predict=predict,
            )
        else:
            acc = PredictionAccuracy(
                actual=df[used_min].iloc[-d_diff.days :],
                predict=predict[: d_diff.days],
            )
        return acc

    @staticmethod
    def _get_pricelist_of_uniq_point_data_for_df(df: pd.DataFrame) -> dict[list[dict]]:
        useddf, newdf = PriceLogChartPreProcessing().data_preprocessing(df=df)

        if not len(useddf) and not len(newdf):
            return {"used": [], "new": []}

        initflag = "initflag"
        result = "result"
        created_at = "x"
        price = "y"
        preprice = "preprice"
        prev = "prev"
        is_continue = "is_continue"

        used = {initflag: True, result: []}
        new = {initflag: True, result: []}

        def set_result(df: pd.DataFrame, target_column: str, result_dict: dict):
            if len(df) == 0:
                return
            for i in range(0, len(df) - 1):
                if i == len(df) - 2:
                    break
                temp_dict = {created_at: df.index[i], price: df[target_column].iloc[i]}
                if temp_dict[price] <= 0:
                    continue
                if result_dict[initflag]:
                    result_dict[initflag] = False
                    result_dict[preprice] = temp_dict[price]
                    result_dict[prev] = temp_dict
                    result_dict[result] = [temp_dict]
                    result_dict[is_continue] = False
                    continue
                if result_dict[preprice] == temp_dict[price]:
                    result_dict[prev] = temp_dict
                    result_dict[is_continue] = True
                    continue
                if (
                    result_dict[is_continue]
                    and result_dict[prev][price] == result_dict[preprice]
                ):
                    result_dict[result].append(result_dict[prev])
                result_dict[is_continue] = False
                result_dict[preprice] = temp_dict[price]
                result_dict[prev] = temp_dict
                result_dict[result].append(temp_dict)
            result_dict[result].append(
                {created_at: df.index[-1], price: df[target_column].iloc[-1]}
            )

        set_result(df=useddf, target_column="used_min", result_dict=used)
        set_result(df=newdf, target_column="new_min", result_dict=new)

        return {"used": used[result], "used_df": useddf, "new": new[result]}


class AddItemUrlPostContext(BaseTemplateValue):
    itemName: str = ""
    urlPath: str = ""
    addSuccess: bool = False
    errmsg: str = ""
    search_query: str | None = None
    POST_ITEM_NAME: str = filter_name.TemplatePostName.ITEM_NAME.value
    POST_URL_PATH: str = filter_name.TemplatePostName.URL_PATH.value

    def __init__(self, adduform: ppi.AddItemUrlForm, db: Session):
        super().__init__(
            itemName=adduform.item_name,
            urlPath=adduform.url_path,
        )
        if not adduform.is_valid():
            self.errmsg = adduform.errmsg
            return
        if adduform.search_query:
            self.search_query = adduform.search_query
        self.add_data(db)

    def add_data(self, db: Session):
        NewestQuery.add_item(item_name=self.itemName, url_path=self.urlPath, db=db)
        self.addSuccess = True


class AddUrlInitContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    errmsg: str = ""
    POST_ITEM_ID: str = filter_name.TemplatePostName.ITEM_ID.value
    POST_URL_PATH: str = filter_name.TemplatePostName.URL_PATH.value
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, adduform: ppi.AddUrlForm):
        super().__init__()
        if not adduform.is_valid_init():
            self.errmsg = adduform.errmsg
            return
        self.item_id = adduform.item_id


class AddUrlPostContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    urlPath: str = ""
    addSuccess: bool = False
    search_query: str | None = None
    errmsg: str = ""
    POST_ITEM_ID: str = filter_name.TemplatePostName.ITEM_ID.value
    POST_URL_PATH: str = filter_name.TemplatePostName.URL_PATH.value
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, adduform: ppi.AddUrlForm, db: Session):
        super().__init__(
            urlPath=adduform.url_path,
        )
        if adduform.item_id != const_value.NONE_ID:
            self.item_id = adduform.item_id
            item = ItemQuery.get_item(db, item_id=self.item_id)
            if not item:
                self.errmsg = "アイテムが見つかりません"
                return
        if not adduform.is_valid():
            self.errmsg = adduform.errmsg
            return
        if adduform.search_query:
            self.search_query = adduform.search_query
        self.add_data(db)

    def add_data(self, db: Session):
        UrlQuery.add_url_and_urlinitem(db, item_id=self.item_id, urlpath=self.urlPath)
        self.addSuccess = True


class UpdateItemNameInitContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    errmsg: str = ""
    pre_item_name: str = ""
    POST_ITEM_ID: str = filter_name.TemplatePostName.ITEM_ID.value
    POST_ITEM_NAME: str = filter_name.TemplatePostName.ITEM_NAME.value
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, upnameform: ppi.UpdateItemNameForm, db: Session):
        super().__init__()
        if upnameform.is_valid_init():
            self.item_id = upnameform.item_id
            item = ItemQuery.get_item(db, item_id=self.item_id)
            if item:
                self.pre_item_name = item.name
            else:
                self.errmsg = "アイテムが見つかりません"
        else:
            self.errmsg = upnameform.errmsg


class UpdateItemNamePostContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    item_name: str = ""
    updateSuccess: bool = False
    errmsg: str = ""
    pre_item_name: str = ""
    POST_ITEM_ID: str = filter_name.TemplatePostName.ITEM_ID.value
    POST_ITEM_NAME: str = filter_name.TemplatePostName.ITEM_NAME.value
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, upnameform: ppi.UpdateItemNameForm, db: Session):
        super().__init__()
        if upnameform.is_valid():
            self.item_name = upnameform.item_name
            self.item_id = upnameform.item_id
            self.update_data(db)
        else:
            self.errmsg = upnameform.errmsg
            if upnameform.item_id != const_value.NONE_ID:
                self.item_id = upnameform.item_id
                item = ItemQuery.get_item(db, item_id=self.item_id)
                if item:
                    self.pre_item_name = item.name
                else:
                    self.errmsg += ", アイテムが見つかりません"

    def update_data(self, db: Session):
        ItemQuery.update_items_name_by_item_id(
            db, item_id=self.item_id, name=self.item_name
        )
        self.updateSuccess = True


class InActAllUrlPostContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    updateSuccess: bool = False
    errmsg: str = ""
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, inactform: ppi.InActAllUrlForm, db: Session):
        super().__init__()
        if inactform.is_valid():
            self.item_id = inactform.item_id
            self.inact_all_url(db)
        else:
            self.errmsg = inactform.errmsg

    def inact_all_url(self, db: Session):
        UrlQuery.update_url_active_all_by_item_id(
            db, item_id=self.item_id, isactive=UrlActive.INACTIVE
        )
        self.updateSuccess = True


class InActUrlPostContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    url_id: int = const_value.NONE_ID
    updateSuccess: bool = False
    errmsg: str = ""
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, inactform: ppi.InActUrlForm, db: Session):
        super().__init__()
        if inactform.is_valid():
            self.item_id = inactform.item_id
            self.url_id = inactform.url_id
            self.inact_url(db)
        else:
            self.errmsg = inactform.errmsg
            if inactform.item_id:
                self.item_id = inactform.item_id
            if inactform.url_id:
                self.url_id = inactform.url_id

    def inact_url(self, db: Session):
        UrlQuery.update_url_active(
            db, item_id=self.item_id, url_id=self.url_id, isactive=UrlActive.INACTIVE
        )
        self.updateSuccess = True


class ActUrlPostContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    url_id: int = const_value.NONE_ID
    updateSuccess: bool = False
    errmsg: str = ""
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, actform: ppi.ActUrlForm, db: Session):
        super().__init__()
        if actform.is_valid():
            self.item_id = actform.item_id
            self.url_id = actform.url_id
            self.act_url(db)
        else:
            self.errmsg = actform.errmsg
            if actform.item_id:
                self.item_id = actform.item_id
            if actform.url_id:
                self.url_id = actform.url_id

    def act_url(self, db: Session):
        UrlQuery.update_url_active(
            db, item_id=self.item_id, url_id=self.url_id, isactive=UrlActive.ACTIVE
        )
        self.updateSuccess = True


class UpdateItemUrlPostContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    updateSuccess: bool = False
    errmsg: str = ""
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, upurlform: ppi.UpdateItemUrlForm, db: Session):
        super().__init__()
        if upurlform.item_id:
            self.item_id = upurlform.item_id
        if not can_item_update(db):
            self.errmsg = "更新できない状態です。サーバを確認して下さい。"
            return
        if upurlform.is_valid():
            self.update_data(upurlform.url_path)
        else:
            self.errmsg = upurlform.errmsg

    def update_data(self, url_path):
        sendTask(ScrOrder.UPDATE, url_path, str(const_value.NONE_ID))
        self.updateSuccess = True


class UpdateItemAllUrlPostContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    updateSuccess: bool = False
    return_user: bool = False
    errmsg: str = ""
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, upurlform: ppi.UpdateItemAllUrlForm, db: Session):
        super().__init__()
        if upurlform.return_user:
            self.return_user = True
        if upurlform.item_id:
            self.item_id = upurlform.item_id
        if not can_item_update(db):
            self.errmsg = "更新できない状態です。サーバを確認して下さい。"
            return
        if upurlform.is_valid():
            self.update_data(db)
        else:
            self.errmsg = upurlform.errmsg

    def update_data(self, db: Session):
        urlinitems = UrlQuery.get_act_urlinfo_by_item_id(db, item_id=self.item_id)
        for uii in urlinitems:
            sendTask(ScrOrder.UPDATE, uii.urlpath, str(const_value.NONE_ID))
        self.updateSuccess = True


class RemoveItemUrlPostContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    updateSuccess: bool = False
    errmsg: str = ""
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, remurlform: ppi.RemoveItemUrlForm, db: Session):
        super().__init__()
        if remurlform.is_valid():
            self.item_id = remurlform.item_id
            self.remove_data(db, url_id=remurlform.url_id)
        else:
            self.errmsg = remurlform.errmsg
            if remurlform.item_id:
                self.item_id = remurlform.item_id

    def remove_data(self, db: Session, url_id: int):
        UrlQuery.delete_urlinitem(db, item_id=self.item_id, url_id=url_id)
        self.updateSuccess = True


class AddGroupPostContext(BaseTemplateValue):
    group_name: str = ""
    group_id: int = const_value.NONE_ID
    errmsg: str = ""
    addSuccess: bool = False
    POST_GROUP_NAME: str = filter_name.TemplatePostName.GROUP_NAME.value
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value

    def __init__(self, addgform: ppi.AddGroupForm, db: Session):
        super().__init__()
        if addgform.is_valid():
            self.group_name = addgform.group_name
            self.add_group(db)
            return
        else:
            self.errmsg = addgform.errmsg
            if addgform.group_name:
                self.group_name = addgform.group_name

    def add_group(self, db: Session):
        if not GroupQuery.get_group_by_name(db, name=self.group_name):
            group_id = GroupQuery.add_group(db, self.group_name)
            if group_id and group_id > const_value.NONE_ID:
                self.group_id = group_id
                self.addSuccess = True
                return
            else:
                self.errmsg = "グループ追加に失敗しました"
                return
        else:
            self.errmsg = "グループ名は既に存在しています"


class EditGroupContext(BaseTemplateValue):
    gfid: int = filter_name.FilterDefault.GID
    other_items: list = []
    other_items_length: int = 0
    group_items: list = []
    group_items_length: int = 0
    groups: list
    actstslist: list
    itemSortList: list
    fquery: dict
    ZAIKO_CHECKED: str = ""
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value
    ITEMACT_NAME: str = filter_name.FilterQueryName.ACT.value
    ITEMSORT_NAME: str = filter_name.FilterQueryName.ISORT.value
    POST_GROUP_ID: str = filter_name.TemplatePostName.GROUP_ID.value
    POST_GROUP_ITEM_LIST: str = filter_name.TemplatePostName.GROUP_ITEM_LIST.value
    STOCK_NAME: str = filter_name.FilterQueryName.ZAIKO.value
    STOCK_VALUE: int = filter_name.FilterOnOff.ON
    MIN_PRICE_RANGE_NAME: str = filter_name.FilterQueryName.PRMIN.value
    MAX_PRICE_RANGE_NAME: str = filter_name.FilterQueryName.PRMAX.value
    MIN_PRICE_RANGE: int | None = None
    MAX_PRICE_RANGE: int | None = None

    def __init__(self, nfqg: ppi.NewestFilterQueryForGroup, db: Session):
        fd = nfqg.get_filter_dict()
        super().__init__(
            actstslist=ppi.get_actstslist(fd),
            itemSortList=ppi.get_item_sort_list(fd),
            groups=ppi.get_groups(db, f=fd),
            fquery=fd,
            ZAIKO_CHECKED=ppi.get_in_stock_filter_checked(fd),
        )

        if filter_name.FilterQueryName.GID.value in self.fquery:
            gid = int(self.fquery[filter_name.FilterQueryName.GID.value])
            self.fquery[filter_name.FilterQueryName.GID.value] = get_gid_in_groups(
                gid=gid, groups=self.groups
            )
            self.gfid = self.fquery[filter_name.FilterQueryName.GID.value]
            self.other_items = NewestQuery.get_newest_data_for_edit_group(
                db, filter=fd, ignore_group_id=gid
            )
            self.other_items_length = len(self.other_items)
            self.group_items = NewestQuery.get_newest_data_of_group(db, group_id=gid)
            self.group_items_length = len(self.group_items)

        if filter_name.FilterQueryName.PRMIN.value in self.fquery:
            self.MIN_PRICE_RANGE = int(
                self.fquery[filter_name.FilterQueryName.PRMIN.value]
            )
        if filter_name.FilterQueryName.PRMAX.value in self.fquery:
            self.MAX_PRICE_RANGE = int(
                self.fquery[filter_name.FilterQueryName.PRMAX.value]
            )


class UpdateGroupItem:
    group_id: int = const_value.NONE_ID

    def __init__(self, giform: ppi.GroupItemUpdateForm, db: Session):
        if giform.is_valid():
            self.group_id = giform.group_id
            self.update_group_item(db, giform.group_item_list)

    def update_group_item(self, db: Session, group_item_list):
        GroupQuery.update_group_item(
            db, group_id=self.group_id, item_list=group_item_list
        )

    def get_query(self):
        if self.group_id and self.group_id != const_value.NONE_ID:
            return f"?{filter_name.FilterQueryName.GID.value}={self.group_id}"
        return ""


class DeleteGroupInitContext(BaseTemplateValue):
    gid: int = const_value.NONE_ID
    groupname: str = ""
    POST_GROUP_ID: str = filter_name.TemplatePostName.GROUP_ID.value
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value

    def __init__(self, delgform: ppi.DeleteGroupForm, db: Session):
        super().__init__()
        if delgform.is_valid():
            self.gid = delgform.group_id
            g = GroupQuery.get_group_by_group_id(db, gid=self.gid)
            self.groupname = g.groupname


class DeleteGroupContext(DeleteGroupInitContext):
    errmsg: str = ""
    delSuccess: bool = False

    def __init__(self, delgform: ppi.DeleteGroupForm, db: Session):
        super().__init__(delgform=delgform, db=db)
        if delgform.is_valid():
            self.delete_group(db)

    def delete_group(self, db: Session):
        GroupQuery.del_group(db, group_id=self.gid)
        self.delSuccess = True


class RenameGroupNameInitContext(BaseTemplateValue):
    gid: int = const_value.NONE_ID
    before_groupname: str = ""
    POST_GROUP_ID: str = filter_name.TemplatePostName.GROUP_ID.value
    POST_GROUP_NAME: str = filter_name.TemplatePostName.GROUP_NAME.value
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value

    def __init__(self, rgnform: ppi.RenameGroupNameInitForm, db: Session):
        super().__init__()
        if rgnform.is_valid():
            self.gid = rgnform.group_id
            g = GroupQuery.get_group_by_group_id(db, gid=self.gid)
            self.before_groupname = g.groupname


class RenameGroupNameContext(BaseTemplateValue):
    gid: int = const_value.NONE_ID
    groupname: str = ""
    updateSuccess: bool = False
    POST_GROUP_ID: str = filter_name.TemplatePostName.GROUP_ID.value
    POST_GROUP_NAME: str = filter_name.TemplatePostName.GROUP_NAME.value
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value

    def __init__(self, rgnform: ppi.RenameGroupNameForm, db: Session):
        super().__init__()
        if rgnform.is_valid():
            self.gid = rgnform.group_id
            self.groupname = rgnform.groupname
            self.rename_group(db)

    def rename_group(self, db: Session):
        GroupQuery.update_group_name(db, group_id=self.gid, name=self.groupname)
        self.updateSuccess = True


class DeleteItemInitContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    itemname: str = ""
    POST_ITEM_ID: str = filter_name.TemplatePostName.ITEM_ID.value
    errmsg: str = ""
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value

    def __init__(self, diform: ppi.DeleteItemForm, db: Session):
        super().__init__()
        if diform.is_valid():
            self.item_id = diform.item_id
            self.itemname = ItemQuery.get_item(db, item_id=self.item_id).name
        else:
            self.errmsg = diform.errmsg


class DeleteItemContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    itemname: str = ""
    POST_ITEM_ID: str = filter_name.TemplatePostName.ITEM_ID.value
    errmsg: str = ""
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value
    delSuccess: bool = False

    def __init__(self, diform: ppi.DeleteItemForm, db: Session):
        super().__init__()
        if not diform.is_valid():
            self.errmsg = diform.errmsg
            return
        self.item_id = diform.item_id
        self.itemname = ItemQuery.get_item(db, item_id=self.item_id).name
        self.delete_data(db)

    def delete_data(self, db: Session):
        ItemQuery.delete_item_relation_by_item_id(db, item_id=self.item_id)
        self.delSuccess = True


class ItemAnalysisPeriod(IdTextSelected):
    pass


class ItemAnalysisContext(BaseTemplateValue):
    item_id: int = const_value.NONE_ID
    analysis_term_id: int = filter_name.AnalysisTermName.ONE_WEEK.id
    period_start: str = ""
    period_end: str = ""
    item_count: database_analysis.CountResult = None
    url_count: database_analysis.CountResult = None
    item_price: database_analysis.PriceResult = None
    url_download: database_analysis.UrlDownLoadResult = None
    store_count: database_analysis.CountResult = None
    store_most_common: database_analysis.StoreMostCommonResult = None
    url_store_count_average: database_analysis.UrlStoreCountAverageResult = None
    analysisPeriodList: list[ItemAnalysisPeriod] = []
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value
    ANALYSIS_Q_NAME: str = filter_name.AnalysisQueryName.ATID.value
    errmsg: str = ""

    def __init__(self, anaq: ppi.AnalysisBaseQuery, db: Session):
        super().__init__()
        if anaq.itemid:
            self.item_id = int(anaq.itemid)
        if anaq.atid:
            self.analysis_term_id = int(anaq.atid)

        if self.isUpdateSystemStatus(db):
            self.errmsg = database_analysis.LogAnalysisError.DATA_IS_BEING_UPDATED.value
            return

        self.analysisPeriodList = self.create_analysis_period_list(
            self.analysis_term_id
        )

        result = database_analysis.get_log_analysis(db=db, atid=self.analysis_term_id)
        if result.is_error():
            self.errmsg = result.get_error().value
            return

        self.period_start = result.get_start_datetime().date()
        self.period_end = result.get_end_datetime().date()

        self.item_count = result.get_item_count()
        self.url_count = result.get_url_count()

        self.item_price = result.get_item_price()

        self.url_download = result.get_url_download()

        self.store_count = result.get_store_count()

        STORE_RANKING_MAX = 5
        self.store_most_common = result.get_store_most_common(
            max_store_num=STORE_RANKING_MAX
        )

        self.url_store_count_average = result.get_url_store_count_average()

    def isUpdateSystemStatus(self, db: Session) -> bool:
        syssts = system_status.SystemStatusAccess()
        syssts.update(db=db)
        if system_status.SystemStatus.DATA_UPDATE == syssts.getStatus():
            return True
        return False

    @staticmethod
    def create_analysis_period_list(analysis_term_id: int):
        analysisPeriodList = []
        for atn in filter_name.AnalysisTermName:
            iap = ItemAnalysisPeriod(id=atn.id, text=atn.jname)
            if analysis_term_id == atn.id:
                iap.selected = templates_string.HTMLOption.SELECTED.value
            analysisPeriodList.append(iap)
        return analysisPeriodList


class ItemPurchaseData(BaseModel):
    item_id: int
    name: str
    urls: dict[str, ItemPurchaseUrl]
    created_at: datetime

    def save_item_purchase_url(self, ipu: ItemPurchaseUrl):
        if ipu.purchase_url in self.urls.keys():
            for itemurl in ipu.itemurls:
                self.urls[ipu.purchase_url].update(itemurl)
        else:
            self.urls[ipu.purchase_url] = ipu

    def get_url_list(self):
        return list(self.urls.values())

    def get_rowspan(self):
        result: int = 0
        for url in self.urls.values():
            result += len(url.itemurls)
        return result


class ItemPurchaseContext(BaseTemplateValue):
    res: list[ItemPurchaseData]
    res_length: int = 0
    ITEMACT_NAME: str = filter_name.FilterQueryName.ACT.value
    actstslist: list
    fquery: dict
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value
    SORT_NAME: str = filter_name.FilterQueryName.PSORT.value
    itemsortlist: list
    groups: list
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value

    def __init__(self, db: Session, pfq: ppi.ItemPurchaseFilterQuery):
        fd = pfq.get_filter_dict()
        super().__init__(
            res=[],
            actstslist=ppi.get_actstslist(fd),
            fquery=fd,
            itemsortlist=ppi.get_item_purchase_sort_list(fd),
            groups=ppi.get_groups(db, f=fd),
        )
        if filter_name.FilterQueryName.GID.value in self.fquery:
            gid = int(self.fquery[filter_name.FilterQueryName.GID.value])
            self.fquery[filter_name.FilterQueryName.GID.value] = get_gid_in_groups(
                gid=gid, groups=self.groups
            )

        self.res = self.create_item_list(
            dbdata=ItemQuery.get_item_and_url_localtime(db, filter=fd),
            domain=read_config.get_support_url()["surugaya"],
        )
        self.res_length = len(self.res)

    def create_item_list(self, dbdata: list, domain: str):
        results_dict: dict[int, ItemPurchaseData] = {}

        for data in dbdata:
            data_dic = dict(data._mapping.items())
            item_id = int(data_dic["item_id"])
            if item_id not in results_dict:
                ipd = ItemPurchaseData(
                    item_id=item_id,
                    name=data_dic["name"],
                    urls={},
                    created_at=data_dic["created_at"],
                )
                results_dict[item_id] = ipd
            else:
                ipd = results_dict[item_id]

            purchase_url = surugayaURL.SurugayaPurchaseURL.get_url(
                urlpath=data_dic["urlpath"], search_word=data_dic["name"]
            )
            ipu = ItemPurchaseUrl(
                itemurls=[
                    ItemUrl(
                        url_id=data_dic["url_id"],
                        item_url=data_dic["urlpath"],
                        act_status=data_dic["active"],
                    )
                ],
                purchase_url=purchase_url,
            )
            ipd.save_item_purchase_url(ipu)
            continue
        return results_dict.values()


class ItemForUrlList(BaseModel):
    item_id: int
    name: str
    act_status: str


class UrlInfoForUrlList(BaseModel):
    url_id: int
    url: str
    name: str | None
    registration_date: datetime
    created_at: datetime | None
    itemlist: list[ItemForUrlList] = []
    item_num: int = 0

    def add_item(self, item: ItemForUrlList):
        if self.itemlist:
            if item.item_id in [i.item_id for i in self.itemlist]:
                return
            self.itemlist.append(item)
        else:
            self.itemlist = [item]
        self.item_num = len(self.itemlist)


class UrlListContext(BaseTemplateValue):
    res: list[UrlInfoForUrlList]
    res_length: int = 0
    ITEMACT_NAME: str = filter_name.FilterQueryName.ACT.value
    actstslist: list
    fquery: dict
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value
    URLSORT_NAME: str = filter_name.FilterQueryName.USORT.value
    urlSortList: list

    def __init__(self, db: Session, ufq: ppi.UrlListFilterQuery):
        fd = ufq.get_filter_dict()
        super().__init__(
            res=[],
            actstslist=ppi.get_actstslist(fd),
            fquery=fd,
            urlSortList=ppi.get_url_sort_list(fd),
        )
        self.res = self.create_url_list(
            res=UrlQuery.get_url_and_item_comb_list_in_local_time(db, filter=fd)
        )
        self.res_length = len(self.res)

    def create_url_list(self, res):
        results: dict[int, UrlInfoForUrlList] = {}
        for r in res:
            d = dict(r._mapping.items())
            url_id = int(d["url_id"])
            if url_id in results:
                newest = self.get_newest_urlinfo(
                    cur=results[url_id], new=self.create_urlinfoforurllist(d)
                )
                if results[url_id] != newest:
                    # reinsert to maintain order
                    results.pop(url_id)
                    results[url_id] = newest
            else:
                results[url_id] = self.create_urlinfoforurllist(d)
            if not d["item_id"]:
                continue
            results[url_id].add_item(self.create_itemforurllist(d))
        return [v for v in results.values()]

    def create_urlinfoforurllist(self, d: dict) -> UrlInfoForUrlList:
        return UrlInfoForUrlList(
            url_id=int(d["url_id"]),
            url=d["urlpath"],
            name=d["uniqname"],
            registration_date=d["registration_date"],
            created_at=d["created_at"],
        )

    def create_itemforurllist(self, d: dict) -> ItemForUrlList | None:
        if not d["item_id"]:
            return None
        return ItemForUrlList(
            item_id=int(d["item_id"]), name=d["itemname"], act_status=d["active"]
        )

    def get_newest_urlinfo(
        self, cur: UrlInfoForUrlList, new: UrlInfoForUrlList
    ) -> dict:
        if not cur.created_at:
            self.move_items(src=cur, dest=new)
            return new
        if not new.created_at:
            return cur
        if cur.created_at >= new.created_at:
            return cur
        else:
            self.move_items(src=cur, dest=new)
            return new

    def move_items(self, src: UrlInfoForUrlList, dest: UrlInfoForUrlList):
        if not src.item_num:
            return
        for i in src.itemlist:
            dest.add_item(i)


class ExtractStoreItemListContext(BaseTemplateValue):
    res: list
    res_length: int = 0
    actstslist: list
    esSortList: list
    groups: list
    storelist: list
    fquery: dict
    ZAIKO_CHECKED: str = ""
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value
    ITEMACT_NAME: str = filter_name.FilterQueryName.ACT.value
    EXST_NAME: str = filter_name.FilterQueryName.EX_STORE.value
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value
    ESSORT_NAME: str = filter_name.FilterQueryName.ESSORT.value
    POST_ITEM_ID: str = filter_name.TemplatePostName.ITEM_ID.value
    POST_GROUP_ID: str = filter_name.TemplatePostName.GROUP_ID.value
    POST_ITEM_ALL_UPDATE: str = filter_name.TemplatePostName.ITEM_ALL_UPDATE.value
    item_all_update_value: str = filter_name.ItemUpdateValue.ITEM_ALL_UPDATE
    POST_RETURN_USER: str = filter_name.TemplatePostName.RETURN_USER.value
    return_user: str = filter_name.FilterOnOff.ON
    STOCK_NAME: str = filter_name.FilterQueryName.ZAIKO.value
    STOCK_VALUE: int = filter_name.FilterOnOff.ON
    MIN_PRICE_RANGE_NAME: str = filter_name.FilterQueryName.PRMIN.value
    MAX_PRICE_RANGE_NAME: str = filter_name.FilterQueryName.PRMAX.value
    MIN_PRICE_RANGE: int | None = None
    MAX_PRICE_RANGE: int | None = None

    def __init__(self, esfq: ppi.ExtractStoreFilterQuery, db: Session):
        fd = esfq.get_filter_dict()
        super().__init__(
            res=self.get_extract_storename_newest_data(db, filter=fd),
            actstslist=ppi.get_actstslist(fd),
            esSortList=ppi.get_extract_store_sort_list(fd),
            groups=ppi.get_groups(db, f=fd),
            storelist=[],
            fquery=fd,
            ZAIKO_CHECKED=ppi.get_in_stock_filter_checked(fd),
        )

        self.res_length = len(self.res)
        self.storelist = pps.get_stores_for_extract_store(db, filter=self.fquery)

        if filter_name.FilterQueryName.GID.value in self.fquery:
            gid = int(self.fquery[filter_name.FilterQueryName.GID.value])
            self.fquery[filter_name.FilterQueryName.GID.value] = get_gid_in_groups(
                gid=gid, groups=self.groups
            )

        if filter_name.FilterQueryName.PRMIN.value in self.fquery:
            self.MIN_PRICE_RANGE = int(
                self.fquery[filter_name.FilterQueryName.PRMIN.value]
            )
        if filter_name.FilterQueryName.PRMAX.value in self.fquery:
            self.MAX_PRICE_RANGE = int(
                self.fquery[filter_name.FilterQueryName.PRMAX.value]
            )

    @staticmethod
    def get_extract_storename_newest_data(db: Session, filter: dict):
        results = []
        db_res = NewestQuery.get_storename_newest_data(db, filter=filter)
        item_grp = {}
        for row in db_res:
            dic = dict(row._mapping.items())
            if dic["item_id"] in item_grp:
                item_grp[dic["item_id"]].append(dic)
            else:
                item_grp[dic["item_id"]] = [dic]

        for item_list in item_grp.values():
            lowest = None
            for item in item_list:
                if not lowest:
                    lowest = item
                    continue
                if item["price"] < lowest["price"]:
                    lowest = item
                    continue
            if lowest:
                results.append(lowest)
        return results


class TermsForListContext(BaseModel):
    terms_id: int = const_value.NONE_ID
    temrs_text: str
    postage: int = 0
    created_at: datetime | None


class StoreForListContext(BaseModel):
    store_id: int = const_value.NONE_ID
    storename: str
    created_at: datetime
    terms_list: list[TermsForListContext]
    terms_num: int

    def __init__(self, store_id: int, storename: str, created_at: datetime):
        super().__init__(
            store_id=store_id,
            storename=storename,
            created_at=created_at,
            terms_list=[],
            terms_num=0,
        )

    def add_terms(self, terms: TermsForListContext):
        self.terms_list.append(terms)
        self.terms_num = len(self.terms_list)


class StoreListContext(BaseTemplateValue):
    res: list[StoreForListContext] = []
    res_length: int = 0
    POST_STORE_ID: str = filter_name.TemplatePostName.STORE_ID.value
    STORESORT_NAME: str = filter_name.FilterQueryName.SORT.value
    storeSortList: list
    fquery: dict
    CONFIGUREDTERMS_NAME: str = filter_name.FilterQueryName.CONFED.value
    confstslist: list

    def __init__(self, db: Session, slfp: ppi.StoreListFilterQuery):
        fq = slfp.get_filter_dict()
        super().__init__(
            fquery=fq,
            storeSortList=ppi.get_store_sort_list(fq),
            confstslist=ppi.get_store_terms_configured_list(fq),
        )
        results = ac_store.StoreQuery.get_store_and_postage_all(db=db, fq=fq)
        self.res = self.convert_to_StoreForListContext(results)
        if not self.res:
            return
        self.res_length = len(self.res)

    @staticmethod
    def convert_to_StoreForListContext(res: list):
        results: dict[int, StoreForListContext] = {}
        for r in res:
            dic = dict(r._mapping.items())
            if not dic["store_id"] in results.keys():
                results[dic["store_id"]] = StoreForListContext(
                    store_id=dic["store_id"],
                    storename=dic["storename"],
                    created_at=dic["created_at"],
                )
            if "terms_id" in dic and str(dic["terms_id"]).isdigit():
                terms_id = int(dic["terms_id"])
                boundary = BoundaryConverter.convert_boundary_to_jtext(dic["boundary"])
                postage = int(dic["postage"])
                terms = TermsForListContext(
                    terms_id=terms_id,
                    temrs_text=boundary,
                    postage=postage,
                    created_at=dic["terms_created_at"],
                )
                results[dic["store_id"]].add_terms(terms)
        return [a for a in results.values()]


class EditShippingConditionContext(BaseTemplateValue):
    item_id_list: list[int]
    store_list: list[SP_StoreShippingTerms]
    errmsg: str = ""
    POST_ITEM_ID: str = filter_name.TemplatePostName.ITEM_ID.value
    POST_STORENAME: str = filter_name.TemplatePostName.STORE_NAME.value
    STORESORT_NAME: str = filter_name.FilterQueryName.SORT.value
    storeSortList: list
    fquery: dict

    def __init__(self, db: Session, slfq: ppi.StoreListFilterQuery):
        fq = slfq.get_filter_dict()
        super().__init__(
            item_id_list=[],
            store_list=[],
            storeSortList=ppi.get_store_sort_list(fq),
            fquery=fq,
        )
        results = ac_store.StoreQuery.get_store_and_postage_all(db, fq=fq)
        if not results or len(results) == 0:
            self.errmsg = "店舗がありません"
            return
        self.store_list = self.convert_to_store_list(results)

    @staticmethod
    def convert_to_store_list(res_list: list[dict]) -> list[SP_StoreShippingTerms]:
        results: dict[str, SP_StoreShippingTerms] = {}
        for row in res_list:
            res = dict(row._mapping.items())
            t = SP_Terms(
                terms_index=res["terms_id"],
                boundary=res["boundary"],
                postage=res["postage"],
                created_at=res["terms_created_at"],
            )
            if res["storename"] in results:
                results[res["storename"]].add_terms(t)
                continue
            else:
                sst = SP_StoreShippingTerms(
                    store_id=res["store_id"],
                    storename=res["storename"],
                )
                results[res["storename"]] = sst
                sst.add_terms(t)
                continue
        return [a for a in results.values()]


class EditShippingConditionResult(BaseTemplateValue):
    update_list: list[StoreForListContext] = []
    delete_list: list[StoreForListContext] = []
    insert_list: list[StoreForListContext] = []
    update_length: int = 0
    delete_length: int = 0
    insert_length: int = 0
    errmsg: str = ""

    def __init__(self, db: Session, escf: ppi.EditShippingConditionForm):
        super().__init__()
        results = ac_store.StoreQuery.get_store_and_postage_all(db)
        self.update_shippingterms_data(db, escf=escf, db_res=results)

    def update_shippingterms_data(
        self, db: Session, escf: ppi.EditShippingConditionForm, db_res: list
    ):
        if len(escf.store_list) == 0:
            self.errmsg = "更新対象がありません"
            return

        storepostage_dict: dict[int, list[m_store.StorePostage]] = {}
        for store in escf.store_list:
            sps_list = store.toStorePostages()
            if len(sps_list) > 0:
                if store.store_id in storepostage_dict:
                    storepostage_dict[store.store_id].extend(sps_list)
                else:
                    storepostage_dict[store.store_id] = sps_list

        non_appear_dest_dict = copy.deepcopy(storepostage_dict)
        update_list: list = []
        delete_list: list = []
        insert_list: list = []
        store_id_to_name: dict[int, str] = {}
        store_id_to_created_at: dict[int, datetime] = {}

        for row in db_res:
            res = dict(row._mapping.items())
            store_id = int(res["store_id"])
            if store_id not in store_id_to_name.keys():
                store_id_to_name[store_id] = res["storename"]
                store_id_to_created_at[store_id] = res["created_at"]
            if "terms_id" not in res or not res["terms_id"]:
                continue
            if store_id in storepostage_dict.keys():
                src_appear = False
                for pos in storepostage_dict[store_id]:
                    if self.is_update_storepostage(pos, res):
                        update_list.append(pos)
                        self.pop_dict(non_appear_dest_dict, store_id, pos.terms_id)
                        src_appear = True
                        continue
                    if self.equal_storepostage(pos, res):
                        self.pop_dict(non_appear_dest_dict, store_id, pos.terms_id)
                        src_appear = True
                        continue
                if src_appear:
                    continue
                sps = self.convert_db_res_to_storepostage(res)
                delete_list.append(sps)
                continue
            sps = self.convert_db_res_to_storepostage(res)
            delete_list.append(sps)
            continue
        insert_list = [
            sps for spslist in non_appear_dest_dict.values() for sps in spslist
        ]

        self.insert_list = self.convert_storepostage_to_StoreForListContext(
            insert_list, store_id_to_name, store_id_to_created_at
        )
        self.insert_length = len(self.insert_list)
        self.update_list = self.convert_storepostage_to_StoreForListContext(
            update_list, store_id_to_name, store_id_to_created_at
        )
        self.update_length = len(self.update_list)
        self.delete_list = self.convert_storepostage_to_StoreForListContext(
            delete_list, store_id_to_name, store_id_to_created_at
        )
        self.delete_length = len(self.delete_list)

        if len(delete_list) > 0:
            ac_store.StoreQuery.delete_storepostage_by_list(db, delete_list=delete_list)
        if len(update_list) > 0:
            ac_store.StoreQuery.update_storepostage_by_list(db, update_list=update_list)
        if len(insert_list) > 0:
            ac_store.StoreQuery.insert_storepostage_list(
                db, storepostage_list=insert_list
            )

    @staticmethod
    def is_update_storepostage(sps: m_store.StorePostage, res: dict):
        if int(res["terms_id"]) == int(sps.terms_id):
            if (
                not res["boundary"]
                and sps.boundary
                or res["boundary"]
                and not sps.boundary
            ):
                return True
            if (
                not res["postage"]
                and sps.postage
                or res["postage"]
                and not sps.boundary
            ):
                return True
            if str(res["boundary"]) != sps.boundary or int(res["postage"]) != int(
                sps.postage
            ):
                return True
        return False

    @staticmethod
    def equal_storepostage(sps: m_store.StorePostage, res: dict):
        if int(res["terms_id"]) == int(sps.terms_id):
            if (
                not res["boundary"]
                and sps.boundary
                or res["boundary"]
                and not sps.boundary
                or str(res["boundary"]) != sps.boundary
            ):
                return False
            if (
                not res["postage"]
                and sps.postage
                or res["postage"]
                and not sps.boundary
                or int(res["postage"]) != int(sps.postage)
            ):
                return False
            return True
        return False

    @staticmethod
    def pop_dict(
        target: dict[int, list[m_store.StorePostage]], store_id: int, terms_id: int
    ):
        if store_id not in target.keys():
            return
        for idx in reversed(range(len(target[store_id]))):
            if terms_id == int(target[store_id][idx].terms_id):
                target[store_id].pop(idx)
                if len(target[store_id]) == 0:
                    target.pop(store_id)
                    break
            continue

    @staticmethod
    def convert_db_res_to_storepostage(res):
        return m_store.StorePostage(
            store_id=int(res["store_id"]),
            terms_id=int(res["terms_id"]),
            boundary=res["boundary"],
            postage=int(res["postage"]),
            created_at=res["terms_created_at"],
        )

    @staticmethod
    def convert_storepostage_to_StoreForListContext(
        res: list[m_store.StorePostage],
        store_id_to_name: dict[int, str],
        store_id_to_created_at: dict[int, datetime],
    ):
        results: dict[int, StoreForListContext] = {}
        for sps in res:
            if sps.store_id not in results.keys():
                results[sps.store_id] = StoreForListContext(
                    store_id=sps.store_id,
                    storename=store_id_to_name[sps.store_id],
                    created_at=store_id_to_created_at[sps.store_id],
                )
            if (
                int(sps.terms_id) >= const_value.INIT_TERMS_ID
                and sps.postage
                and sps.boundary
            ):
                boundary = BoundaryConverter.convert_boundary_to_jtext(sps.boundary)
                created_at = sps.created_at
                if not created_at:
                    created_at = cm_util.utcTolocaltime(datetime.now(timezone.utc))
                terms = TermsForListContext(
                    terms_id=sps.terms_id,
                    temrs_text=boundary,
                    postage=sps.postage,
                    created_at=created_at,
                )
                results[sps.store_id].add_terms(terms)
        return [a for a in results.values()]


class DeleteStoreInitContext(BaseTemplateValue):
    store_id: int = const_value.NONE_ID
    storename: str = ""
    errmsg: str = ""
    delete_list: list[StoreForListContext] = []
    POST_STORE_ID: str = filter_name.TemplatePostName.STORE_ID.value

    def __init__(self, db: Session, dsf: ppi.DeleteStoreForm):
        super().__init__()
        if not dsf.is_valid():
            self.errmsg = dsf.errmsg
            return
        self.store_id = dsf.store_id

        results = ac_store.StoreQuery.get_store_and_postage_by_item_id(
            db=db, item_id=self.store_id
        )
        self.delete_list = StoreListContext.convert_to_StoreForListContext(results)
        self.storename = self.get_storename_in_results(results)

    @staticmethod
    def get_storename_in_results(res: list):
        for r in res:
            dic = dict(r._mapping.items())
            if (
                "storename" in dic.keys()
                and dic["storename"]
                and len(dic["storename"]) > 0
            ):
                return dic["storename"]
        return ""


class DeleteStoreContext(BaseTemplateValue):
    storename: str = ""
    errmsg: str = ""
    delSuccess: bool = False

    def __init__(self, db: Session, dsf: ppi.DeleteStoreForm):
        super().__init__()
        if not dsf.is_valid():
            self.errmsg = dsf.errmsg
            return
        self.storename = ac_store.StoreQuery.get_storename_by_store_id(
            db=db, store_id=dsf.store_id
        )
        self.delete_store_and_postage(db=db, store_id=dsf.store_id)
        self.delSuccess = True

    @classmethod
    def delete_store_and_postage(cls, db: Session, store_id: int):
        ac_store.StoreQuery.delete_storepostage_by_store_id_list(
            db=db, store_id_list=[store_id]
        )
        ac_store.StoreQuery.delete_store_by_store_id(db=db, store_id=store_id)


class OnlineTermsForListContext(BaseModel):
    terms_id: int = const_value.NONE_ID
    pref: str = ""
    temrs_text: str
    postage: int = 0
    created_at: datetime | None
    campaign_msg: str = ""


class OnlineStoreForListContext(BaseModel):
    shop_id: int = const_value.NONE_ID
    storename: str
    created_at: datetime
    terms_list: list[OnlineTermsForListContext]
    terms_num: int
    shipping_url: str

    def __init__(
        self, shop_id: int, storename: str, created_at: datetime, shipping_url: str
    ):
        super().__init__(
            shop_id=shop_id,
            storename=storename,
            created_at=created_at,
            terms_list=[],
            terms_num=0,
            shipping_url=shipping_url,
        )

    def add_terms(self, terms: OnlineTermsForListContext):
        self.terms_list.append(terms)
        self.terms_num = len(self.terms_list)


class OnlineStoreListContext(BaseTemplateValue):
    res: list[OnlineStoreForListContext]
    res_length: int = 0
    STORESORT_NAME: str = filter_name.FilterQueryName.SORT.value
    storeSortList: list
    fquery: dict
    CONFIGUREDTERMS_NAME: str = filter_name.FilterQueryName.CONFED.value
    confstslist: list
    PREF_NAME: str = filter_name.FilterQueryName.PREF.value
    pref_list: list[IdTextSelected]
    EQST_NAME: str = filter_name.FilterQueryName.STORE.value
    storelist: list[pps.TemplatesStore]
    ONLINE_STORE_COPY_NAME: str = filter_name.FilterQueryName.OSCTYPE.value
    online_store_copy_type_list: list[IdTextSelected]
    pref_list_for_copy: list[IdTextSelected]

    def __init__(self, db: Session, slfp: ppi.OnlineStoreListFilterQuery):
        fq = slfp.get_filter_dict()
        super().__init__(
            res=[],
            fquery=fq,
            storeSortList=ppi.get_store_sort_list(fq),
            confstslist=ppi.get_store_terms_configured_list(fq),
            pref_list=[],
            storelist=self.create_storelist(db, fq=fq),
            online_store_copy_type_list=self.create_osctypelist(),
            pref_list_for_copy=[],
        )
        pref_dict = self.create_pref_id_to_prefname(db)
        self.pref_list = self.create_selected_pref_list(pref_dict, fq=fq)
        self.pref_list_for_copy = self.convert_to_pref_list_for_copy(pref_dict)
        results = ac_store.OnlineStoreQuery.get_all_local_time_by_query(db=db, fq=fq)
        self.res = self.convert_to_OnlineStoreForListContext(
            pref_id_to_prefname=pref_dict, res=results
        )
        if not self.res:
            return
        self.res_length = len(self.res)

    @classmethod
    def convert_to_OnlineStoreForListContext(cls, pref_id_to_prefname: dict, res: list):
        results: dict[int, OnlineStoreForListContext] = {}
        for r in res:
            dic = dict(r._mapping.items())
            if not dic["shop_id"] in results.keys():
                results[dic["shop_id"]] = OnlineStoreForListContext(
                    shop_id=dic["shop_id"],
                    storename=dic["storename"],
                    created_at=dic["created_at"],
                    shipping_url=surugayaURL.SurugayaShippingURL(
                        tenpo_code=dic["tenpo_code"]
                    ).get_url(),
                )
            if "terms_id" in dic and str(dic["terms_id"]).isdigit():
                pref = pref_id_to_prefname[int(dic["pref_id"])]
                terms_id = int(dic["terms_id"])
                boundary = BoundaryConverter.convert_boundary_to_jtext(dic["boundary"])
                postage = int(dic["postage"])
                campaign_msg = dic["campaign_msg"]
                terms = OnlineTermsForListContext(
                    terms_id=terms_id,
                    temrs_text=boundary,
                    pref=pref,
                    postage=postage,
                    created_at=dic["terms_created_at"],
                    campaign_msg=campaign_msg,
                )
                results[dic["shop_id"]].add_terms(terms)
        return [a for a in results.values()]

    def create_pref_id_to_prefname(self, db: Session):
        ret = ac_store.PrefectureQuery.get_all(db)
        results: dict[int, str] = {}
        for r in ret:
            if r.pref_id not in results:
                results[r.pref_id] = r.name
        return results

    def create_selected_pref_list(self, pref_dict: dict[int, str], fq: dict):
        pref_name_q = None
        if filter_name.FilterQueryName.PREF.value in fq:
            pref_name_q = fq[filter_name.FilterQueryName.PREF.value]
        results: list[IdTextSelected] = []
        for pref_id, prefname in pref_dict.items():
            its = IdTextSelected(id=pref_id, text=prefname)
            if pref_name_q and prefname == pref_name_q:
                its.selected = templates_string.HTMLOption.SELECTED.value
            results.append(its)
        return results

    def convert_to_pref_list_for_copy(self, pref_dict: dict[int, str]):
        default_pref_name = read_config.get_default_shipping_prefecture_name()
        results: list[IdTextSelected] = []
        for pref_id, prefname in pref_dict.items():
            if prefname == PrefectureName.get_country_wide_name():
                continue
            its = IdTextSelected(id=pref_id, text=prefname)
            if prefname == default_pref_name:
                its.selected = templates_string.HTMLOption.SELECTED.value
            results.append(its)
        return results

    def create_storelist(self, db: Session, fq: dict):
        oslist = ac_store.OnlineStoreQuery.get_onlinestore_all_sorted_by_storename(db)
        if not oslist:
            return []
        results: list[pps.TemplatesStore] = []
        for store in oslist:
            ts = pps.TemplatesStore(id=store.shop_id, name=store.storename)
            if filter_name.FilterQueryName.STORE.value in fq and ts.id == int(
                fq[filter_name.FilterQueryName.STORE.value]
            ):
                ts.selected = templates_string.HTMLOption.SELECTED.value
            results.append(ts)
        return results

    @classmethod
    def create_osctypelist(cls):
        return [
            IdTextSelected(id=osct.id, text=osct.jname)
            for osct in filter_name.OnlineStoreCopyTypeName
        ]


class OnlineStoreCopyContext(BaseTemplateValue):
    insert_list: list[StoreForListContext] = []
    insert_length: int = 0

    def __init__(self, db: Session, oscq: ppi.OnlineStoreCopyToMyQuery):
        super().__init__()
        dict_for_slc = (
            online_store_copy.OnlineStoreCopy.copy_online_store_postage_to_local(
                db=db, osct_id=oscq.online_store_copy_type, pref_name=oscq.pref
            )
        )
        self.insert_list = (
            EditShippingConditionResult.convert_storepostage_to_StoreForListContext(
                res=dict_for_slc["res"],
                store_id_to_name=dict_for_slc["store_id_to_name"],
                store_id_to_created_at=dict_for_slc["store_id_to_created_at"],
            )
        )
        if self.insert_list:
            self.insert_length = len(self.insert_list)


class OnlineStoreUpdateContext(BaseTemplateValue):
    errmsg: str = ""

    def __init__(self, db: Session):
        super().__init__()
        self.update_online_store(db)

    def update_online_store(self, db: Session):
        syssts = get_sys_status.getSystemStatus(db)
        if syssts == system_status.SystemStatus.DATA_UPDATE.name:
            self.errmsg = "サーバが更新中です。店舗情報を更新できません。"
            return
        if syssts != system_status.SystemStatus.ACTIVE.name:
            self.errmsg = "更新できない状態です。サーバを確認して下さい。"
            return
        sendTask(ScrOrder.UPDATE_ONLINE_STORE_POSTAGE, "", "")

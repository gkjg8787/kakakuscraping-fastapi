from typing import List, Dict, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from common import (
    filter_name,
    templates_string,
    read_config,
)
from template_value import BaseTemplateValue
import parameter_parser.item as ppi
import parameter_parser.store as pps
import parameter_parser.calcitemcomb as ppc
from accessor.item import (
    NewestQuery,
)
from itemcomb.storepostage import (
    getAndRegistShippingTermsByItemId,
    StorePostageResultName,
    update_shippingterms,
)
from itemcomb.sumitemcomb_adapt import startCalcSumitemComb
import model.store as mstore

from itemcomb import surugaya_postage_util as spu
from itemcomb.surugaya_postage.const_value import DEFAULT_PREF

from template_value.storepostage import (
    StoreShippingTerms,
    Terms,
)


class ItemSelectionContext(BaseTemplateValue):
    res: List
    res_length: int = 0
    actstslist: List
    itemSortList: List
    groups: List
    storelist: List
    fquery: Dict
    ZAIKO_CHECKED: str = ""
    GROUPID_NAME: str = filter_name.FilterQueryName.GID.value
    ITEMACT_NAME: str = filter_name.FilterQueryName.ACT.value
    ITEMSORT_NAME: str = filter_name.FilterQueryName.ISORT.value
    EQST_NAME: str = filter_name.FilterQueryName.STORE.value
    ITEMID_Q_NAME: str = filter_name.ItemDetailQueryName.ITEMID.value
    ITEM_LIMIT: int = 0
    STOCK_NAME: str = filter_name.FilterQueryName.ZAIKO.value
    STOCK_VALUE: int = filter_name.FilterOnOff.ON
    MIN_PRICE_RANGE_NAME: str = filter_name.FilterQueryName.PRMIN.value
    MAX_PRICE_RANGE_NAME: str = filter_name.FilterQueryName.PRMAX.value
    MIN_PRICE_RANGE: Optional[int] = None
    MAX_PRICE_RANGE: Optional[int] = None

    def __init__(self, request, nfq: ppi.NewestFilterQuery, db: Session):
        fd = nfq.get_filter_dict()
        super().__init__(
            request=request,
            res=NewestQuery.get_newest_data(db, filter=fd),
            actstslist=ppi.get_actstslist(fd),
            itemSortList=ppi.get_item_sort_list(fd),
            groups=ppi.get_groups(db, f=fd),
            storelist=[],
            fquery=fd,
            ZAIKO_CHECKED=ppi.get_in_stock_filter_checked(fd),
        )
        item_limit = read_config.get_itemcomb_select_limit()
        if item_limit and str(item_limit).isdigit() and int(item_limit) > 0:
            self.ITEM_LIMIT = int(item_limit)
        self.res_length = len(self.res)
        self.storelist = pps.get_stores_for_newest(db, filter=self.fquery)

        if filter_name.FilterQueryName.GID.value in self.fquery:
            gid = int(self.fquery[filter_name.FilterQueryName.GID.value])

            def get_exist_gid(gid):
                for g in self.groups:
                    if g.group_id == gid:
                        return gid
                return filter_name.FilterDefault.GID

            self.fquery[filter_name.FilterQueryName.GID.value] = get_exist_gid(gid)

        if filter_name.FilterQueryName.PRMIN.value in self.fquery:
            self.MIN_PRICE_RANGE = int(
                self.fquery[filter_name.FilterQueryName.PRMIN.value]
            )
        if filter_name.FilterQueryName.PRMAX.value in self.fquery:
            self.MAX_PRICE_RANGE = int(
                self.fquery[filter_name.FilterQueryName.PRMAX.value]
            )


class ShippingConditionContext(BaseTemplateValue):
    item_id_list: List[int] = []
    store_list: List = []
    errmsg: str = ""
    POST_ITEM_ID: str = filter_name.TemplatePostName.ITEM_ID.value
    POST_STORENAME: str = filter_name.TemplatePostName.STORE_NAME.value

    def __init__(self, request, scq: ppc.ShippingConditionQuery, db: Session):
        super().__init__(request=request)
        if not scq.is_valid():
            self.errmsg = scq.errmsg
            return
        conf_item_limit = read_config.get_itemcomb_select_limit()
        if (
            conf_item_limit
            and str(conf_item_limit).isdigit()
            and int(conf_item_limit) > 0
        ):
            item_limit = int(conf_item_limit)
            if len(scq.item_id_list) > item_limit:
                self.errmsg = f"選択したアイテム数が上限を超えています（上限：{item_limit}）"
                return
        self.item_id_list = scq.item_id_list
        results = getAndRegistShippingTermsByItemId(db, itemids=self.item_id_list)
        if StorePostageResultName.ERROR in results:
            self.errmsg = results[StorePostageResultName.ERROR].value
            return
        if StorePostageResultName.RESULT in results:
            self.store_list = self.convert_to_store_list(
                results[StorePostageResultName.RESULT]
            )

    def convert_to_store_list(self, res_list: List[Dict]) -> List[StoreShippingTerms]:
        results: Dict[str, StoreShippingTerms] = {}
        for res in res_list:
            t = Terms(
                terms_index=res["terms_id"],
                boundary=res["boundary"],
                postage=res["postage"],
                created_at=res["created_at"],
            )
            if res["storename"] in results:
                results[res["storename"]].add_terms(t)
                continue
            else:
                sst = StoreShippingTerms(
                    store_id=res["store_id"],
                    storename=res["storename"],
                )
                results[res["storename"]] = sst
                sst.add_terms(t)
                continue
        return [a for a in results.values()]


class ResultItem(BaseModel):
    item_number: int
    item_name: str = ""
    store_name: str = ""
    item_price: int


class ResultStoreItem(BaseModel):
    name: str
    price: int


class ResultStore(BaseModel):
    name: str
    sum_pos_out: int
    postage: int
    sum_pos_in: int
    items: List[ResultStoreItem] = []


class ItemCombCalcResultContext(BaseTemplateValue):
    item_count: int = 0
    itemnames: str = ""
    sum_pos_in: str = ""
    sum_postage: str = ""
    item_list: List[ResultItem] = []
    store_list: List = []
    proc_time: str = "0"

    def __init__(self, request, icrf: ppc.ItemCombinationResultForm, db: Session):
        super().__init__(request=request)
        if not icrf.is_valid() or len(icrf.store_list) == 0:
            return
        self.update_shippingterms_data(db, icrf=icrf)
        # print(f"icrf.store_list={icrf.store_list}")
        res = startCalcSumitemComb(db, itemidlist=icrf.item_id_list)
        # print(f"res={res}")
        self.set_convert_result(res)

    def set_convert_result(self, res: dict):
        storeres = {}
        for k, v in res.items():
            if k == "sum_pos_in":
                self.sum_pos_in = v
                continue
            if k == "sum_postage":
                self.sum_postage = v
                continue
            if k == "errmsg":
                continue
            if k == "proc_time":
                self.proc_time = f"{v:.3f}"
                continue
            storeres[k] = v
        self.item_list = self._create_item_list(storeres)
        self.store_list = self._create_store_list(storeres)
        self._set_item_names_count(storeres)

    def _create_store_list(self, storeres):
        results: List[ResultStore] = []
        for storename, val in storeres.items():
            rs = ResultStore(
                name=str(storename),
                sum_pos_out=int(val["sum_pos_out"]),
                postage=int(val["postage"]),
                sum_pos_in=int(val["sum_pos_out"]) + int(val["postage"]),
                items=list(),
            )
            for item in storeres[storename]["items"]:
                rsi = ResultStoreItem(
                    name=item["itemname"],
                    price=item["price"],
                )
                rs.items.append(rsi)
            results.append(rs)
        return results

    def _create_item_list(self, storeres):
        item_num = 0
        results: List[ResultItem] = []
        for storename in storeres:
            for item in storeres[storename]["items"]:
                results.append(
                    ResultItem(
                        item_number=item_num,
                        item_name=item["itemname"],
                        store_name=storename,
                        item_price=item["price"],
                    )
                )
                item_num += 1
        return results

    def _set_item_names_count(self, storeres):
        items = []
        for k, v in storeres.items():
            for val in v["items"]:
                items.append(val["itemname"])
                self.item_count += 1
        self.itemnames = "、".join(items)

    @staticmethod
    def update_shippingterms_data(db: Session, icrf: ppc.ItemCombinationResultForm):
        store_id_list: List[int] = []
        storepostage_list: List[mstore.StorePostage] = []
        for store in icrf.store_list:
            store_id_list.append(store.store_id)
            sps = store.toStorePostages()
            if len(sps) > 0:
                storepostage_list.extend(sps)

        update_shippingterms(
            db=db, store_id_list=store_id_list, storepostage_list=storepostage_list
        )


class SearchShippingResult(BaseModel):
    shop_name: str = ""
    url: str = ""
    shop_id: int
    postage: int | None = None


class DestinationPrefecture(BaseModel):
    name: str = ""
    selected: str = ""


class SearchShippingContext(BaseTemplateValue):
    PREF_NAME: str = filter_name.FilterQueryName.PREF.value
    SEARCH_WORD_NAME: str = filter_name.FilterQueryName.WORD.value
    sword: str = ""
    pref_list: List[str] = []
    search_result: List = []
    errmsg: str = ""

    def __init__(self, request, ssq: ppc.SearchShippingQuery, db: Session):
        super().__init__(request=request)
        if not ssq.pref:
            pref = DEFAULT_PREF
        else:
            pref = ssq.pref
        # print(pref)
        raw_pref_list = spu.getPrefList()
        self.pref_list = self.create_pref_list(raw_pref_list, pref)
        self.sword = ssq.word
        if not ssq.is_valid():
            self.errmsg = ssq.errmsg
            return
        self.search_result = self.cretate_search_result(
            db=db, storename=ssq.word, prefectures=[pref]
        )
        if len(self.search_result) == 0:
            self.errmsg = "見つかりませんでした"
            return

    def create_pref_list(self, raw_pref_list, query_pref: str):
        results: List[DestinationPrefecture] = []
        for pref in raw_pref_list:
            dp = DestinationPrefecture(name=pref)
            if pref == query_pref:
                dp.selected = templates_string.HTMLOption.SELECTED.value
            results.append(dp)
        return results

    def cretate_search_result(
        self, db: Session, storename: str, prefectures: list[str]
    ):
        if not prefectures:
            return []
        res = spu.get_shippingResult(
            db=db, storename=storename, prefectures=prefectures
        )
        results: list[SearchShippingResult] = []
        for r in res.get_list():
            ssr = SearchShippingResult(
                shop_id=r.shop_id,
                url=r.url,
                shop_name=r.shop_name,
                postage=r.get_prefecture_postage(prefectures[0]),
            )
            results.append(ssr)

        return results

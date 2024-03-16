import re
from dataclasses import dataclass
from .sumitem import SumItem, Store, SelectItem, StoreOperator


class PriceComparitionMargin:
    margintype: str
    marginvalue: str
    minmargin: str

    def __init__(self, options_dict: dict):
        if "type" not in options_dict:
            self.margintype = "fix"
        if "fix" == options_dict["type"] or "rate" == options_dict["type"]:
            self.margintype = options_dict["type"]
        if "value" in options_dict:
            if self.margintype == "fix" and int(options_dict["value"]) >= 0:
                self.marginvalue = options_dict["value"]
            elif self.margintype == "rate" and float(options_dict["value"]) >= 0:
                self.marginvalue = options_dict["value"]
        if "min-value" in options_dict and int(options_dict["min-value"]) >= 0:
            self.minmargin = options_dict["min-value"]

    def get_margin(self, price: int) -> int:
        if self.margintype == "fix":
            return int(self.marginvalue)
        if self.margintype == "rate":
            margin = float(price) * float(self.marginvalue)
            if int(margin) > int(self.minmargin):
                return int(margin)
            return int(self.minmargin)
        return 0


@dataclass
class SearchcombCommand:
    storeconf: dict
    itemlist: list[dict]
    options: PriceComparitionMargin


def createStoreCatalog(storeconf: dict):
    storecatalog: list[Store] = []
    pattern = r"([0-9]*)([<|>]=?)"
    comp = re.compile(pattern)
    for store in storeconf.keys():
        sobj = Store(store)
        for boundary in storeconf[store]:
            bv = comp.findall(boundary["boundary"])
            if len(bv) == 1:
                # print('bv=({}, {})'.format(bv[0], bv[1]))
                ope = StoreOperator.create(bv[0][0], bv[0][1], boundary["postage"])
            elif len(bv) == 2:
                ope = StoreOperator.createRange(
                    bv[0][0], bv[0][1], bv[1][0], bv[1][1], boundary["postage"]
                )
            else:
                print("Error not support format : {}".format(boundary["boundary"]))
                continue
            sobj.addPostage(ope)
        storecatalog.append(sobj)
    return storecatalog


def printStoreCatalog(storeconf: dict):
    stca = createStoreCatalog(storeconf)
    for st in stca:
        print("---{}---".format(st.getName()))
        print("set price={} => postage={}".format(500, st.getPostage(500)))
        print("set price={} => postage={}".format(1500, st.getPostage(1500)))
        print("set price={} => postage={}".format(3900, st.getPostage(3900)))
        print("set price={} => postage={}".format(8100, st.getPostage(8100)))


def createSelectItem(item: dict):
    return SelectItem(item["itemname"], item["storename"], item["price"])


# @stop_watch
def makeComb(ary1, *args):
    def arycomb(a, b):
        if len(b) == 0:
            return a
        if len(a) > 0 and hasattr(a[0], "__iter__"):
            retary = [[*ia, ib] for ia in a for ib in b]
        else:
            retary = [[ia, ib] for ia in a for ib in b]
        return retary

    retary = ary1
    if len(args) == 0:
        return [[i] for i in retary]

    for a in args:
        if not isinstance(a, list) and not isinstance(a, tuple):
            return retary
        retary = arycomb(retary, a)
    return retary


def getStore(stca: list[Store], name: str):
    for s in stca:
        if name == s.getName():
            return s
    return None


# 送料込みで高いものを排除
def removeHighPriceItem(
    stca: list[Store], ngrp: list, itemlist: list[dict], pcm: PriceComparitionMargin
):
    posin_mingrp = []
    MARGIN_PRICE = 250
    for ptn in ngrp:
        minv = -1
        min_idx = -1
        for i in ptn:
            store = getStore(stca, itemlist[i]["storename"])
            price = int(itemlist[i]["price"])
            sump = price + store.getPostage(price)
            if minv == -1 or minv > sump:
                minv = sump
                min_idx = i
        posin_mingrp.append({"midx": min_idx, "mval": minv})
    # print('postage include mingrp = {}'.format(posin_mingrp))
    newngrp = []
    for ptn, mindict in zip(ngrp, posin_mingrp):
        ary = []
        for i in ptn:
            if int(mindict["midx"]) == int(i):
                ary.append(i)
                continue
            # 送料込みの最安値よりも基本価格が高いものは追加しない
            # 閾値の近くだと複数のアイテム選択時に送料込みで逆転する場合があるため余裕を持たせる
            if int(mindict["mval"]) + pcm.get_margin(int(mindict["mval"])) >= int(
                itemlist[i]["price"]
            ):
                ary.append(i)
        newngrp.append(ary)
    return newngrp


# アイテム名でグループ分けしてインデックス配列を作成
def createItemPtn(itemlist: list[dict]):
    ngrp = {}
    for i, item in enumerate(itemlist):
        if item["itemname"] in ngrp.keys():
            ngrp[item["itemname"]].append(i)
        else:
            ngrp[item["itemname"]] = [i]
    return list(ngrp.values())


# @stop_watch
def createBulkBuy(cmd: SearchcombCommand):
    bulk: list[SumItem] = []
    # ws = wantItemSet(itemlist)
    stca = createStoreCatalog(cmd.storeconf)
    itemptn = createItemPtn(cmd.itemlist)
    argary = removeHighPriceItem(stca, itemptn, cmd.itemlist, cmd.options)
    # ary1 = [i for i in range(len(itemlist))]
    # argary = [ary1 for i in range(len(ws))]
    # mc = makeComb(ary1, *argary)
    mc = makeComb(*argary)
    for comb in mc:
        ptn = SumItem(stca)
        for ind in comb:
            # if ptn.existItemName(itemlist[ind]['itemname']):
            #    break
            item = createSelectItem(cmd.itemlist[ind])
            ptn.addItem(item)
        # if ptn.getItemlen() == len(ws):
        bulk.append(ptn)
    return bulk


def wantItemSet(itemlist):
    lret = [a["itemname"] for a in itemlist]
    return set(lret)


def saitekiPrice(cmd: SearchcombCommand):
    retdict = {}
    ws = wantItemSet(cmd.itemlist)
    retdict["ws_len"] = len(ws)
    # for i in ws: print(i)
    bulk = createBulkBuy(cmd)
    retdict["bulk_len"] = len(bulk)
    cheapest = None
    bestprice = -1
    for i, b in enumerate(bulk):
        sumprice = b.getSum()
        if bestprice == -1 or bestprice > sumprice:
            cheapest = b
            bestprice = sumprice
        # print('----[{}]----start---'.format(i))
        # b.printSum()
        # print('----[{}]-----end----'.format(i))
    retdict["lowest_sum"] = cheapest
    # print('---best price---')
    # print('price={}'.format(bestprice))
    # cheapest.printSum()
    return retdict


def searchcomb(cmd: SearchcombCommand):
    if len(cmd.storeconf) == 0:
        return {"errmsg": "no storeconf"}
    if len(cmd.itemlist) == 0:
        return {"errmsg": "no itemlist"}
    res = saitekiPrice(cmd)
    if res["lowest_sum"] is None:
        return {}
    return res["lowest_sum"].getdict()

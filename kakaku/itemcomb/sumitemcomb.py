import re
import itertools
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


def getStore(stca: list[Store], name: str):
    for s in stca:
        if name == s.getName():
            return s
    return None


def removeHighPriceItem(
    stca: list[Store], ngrp: list, itemlist: list[dict], pcm: PriceComparitionMargin
):
    posin_mingrp = []
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
    newngrp = []
    for ptn, mindict in zip(ngrp, posin_mingrp):
        ary = []
        for i in ptn:
            if int(mindict["midx"]) == int(i):
                ary.append(i)
                continue
            if int(mindict["mval"]) + pcm.get_margin(int(mindict["mval"])) >= int(
                itemlist[i]["price"]
            ):
                ary.append(i)
        newngrp.append(ary)
    return newngrp


def createItemPtn(itemlist: list[dict]):
    ngrp = {}
    for i, item in enumerate(itemlist):
        if item["itemname"] in ngrp.keys():
            ngrp[item["itemname"]].append(i)
        else:
            ngrp[item["itemname"]] = [i]
    return list(ngrp.values())


def createBulkBuy(cmd: SearchcombCommand):
    bulk: list[SumItem] = []
    stca = createStoreCatalog(cmd.storeconf)
    itemptn = createItemPtn(cmd.itemlist)
    argary = removeHighPriceItem(stca, itemptn, cmd.itemlist, cmd.options)
    mc = itertools.product(*argary)
    for comb in mc:
        ptn = SumItem(stca)
        for ind in comb:
            item = createSelectItem(cmd.itemlist[ind])
            ptn.addItem(item)
        bulk.append(ptn)
    return bulk


def wantItemSet(itemlist):
    lret = [a["itemname"] for a in itemlist]
    return set(lret)


def saitekiPrice(cmd: SearchcombCommand):
    retdict = {}
    ws = wantItemSet(cmd.itemlist)
    retdict["ws_len"] = len(ws)
    bulk = createBulkBuy(cmd)
    retdict["bulk_len"] = len(bulk)
    cheapest = None
    bestprice = -1
    for i, b in enumerate(bulk):
        sumprice = b.getSum()
        if bestprice == -1 or bestprice > sumprice:
            cheapest = b
            bestprice = sumprice
    retdict["lowest_sum"] = cheapest
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

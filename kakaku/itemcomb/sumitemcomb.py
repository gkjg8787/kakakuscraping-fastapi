import re
from .sumitem import SumItem, Store, SelectItem, StoreOperator


def createStoreCatalog(storeconf):
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


def printStoreCatalog(storeconf):
    stca = createStoreCatalog(storeconf)
    for st in stca:
        print("---{}---".format(st.getName()))
        print("set price={} => postage={}".format(500, st.getPostage(500)))
        print("set price={} => postage={}".format(1500, st.getPostage(1500)))
        print("set price={} => postage={}".format(3900, st.getPostage(3900)))
        print("set price={} => postage={}".format(8100, st.getPostage(8100)))


def createSelectItem(item):
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


def getStore(stca, name):
    for s in stca:
        if name == s.getName():
            return s
    return None


# 送料込みで高いものを排除
def removeHighPriceItem(stca, ngrp, itemlist):
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
            if int(mindict["mval"]) + MARGIN_PRICE >= int(itemlist[i]["price"]):
                ary.append(i)
        newngrp.append(ary)
    return newngrp


# アイテム名でグループ分けしてインデックス配列を作成
def createItemPtn(itemlist):
    ngrp = {}
    for i, item in enumerate(itemlist):
        if item["itemname"] in ngrp.keys():
            ngrp[item["itemname"]].append(i)
        else:
            ngrp[item["itemname"]] = [i]
    return list(ngrp.values())


# @stop_watch
def createBulkBuy(itemlist, storeconf):
    bulk: list[SumItem] = []
    # ws = wantItemSet(itemlist)
    stca = createStoreCatalog(storeconf)
    itemptn = createItemPtn(itemlist)
    argary = removeHighPriceItem(stca, itemptn, itemlist)
    # ary1 = [i for i in range(len(itemlist))]
    # argary = [ary1 for i in range(len(ws))]
    # mc = makeComb(ary1, *argary)
    mc = makeComb(*argary)
    for comb in mc:
        ptn = SumItem(stca)
        for ind in comb:
            # if ptn.existItemName(itemlist[ind]['itemname']):
            #    break
            item = createSelectItem(itemlist[ind])
            ptn.addItem(item)
        # if ptn.getItemlen() == len(ws):
        bulk.append(ptn)
    return bulk


def wantItemSet(itemlist):
    lret = [a["itemname"] for a in itemlist]
    return set(lret)


def saitekiPrice(itemlist, storeconf):
    retdict = {}
    ws = wantItemSet(itemlist)
    retdict["ws_len"] = len(ws)
    # for i in ws: print(i)
    bulk = createBulkBuy(itemlist, storeconf)
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


def searchcomb(storeconf, itemlist):
    if len(storeconf) == 0:
        return {"errmsg": "no storeconf"}
    if len(itemlist) == 0:
        return {"errmsg": "no itemlist"}
    res = saitekiPrice(itemlist, storeconf)
    if res["lowest_sum"] is None:
        return {}
    return res["lowest_sum"].getdict()

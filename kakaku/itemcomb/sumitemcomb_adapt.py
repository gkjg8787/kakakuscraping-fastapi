import os
import time
import re

from sqlalchemy.orm import Session
import pulp

from accessor.item import (
    ItemQuery,
)
from accessor.store import StoreQuery
from common import cmnlog


def convert_shipping_rules(conf: dict):
    shipping_rules = {}

    for store, rules in conf.items():
        # 1. 各ルールを (開始, 終了, 送料) の形に解析する
        parsed_intervals = []
        event_points = {0}  # すべての境界値を記録するセット（0は必須）

        for rule in rules:
            boundary = rule["boundary"]
            postage = int(rule["postage"])
            nums = [int(n) for n in re.findall(r"\d+", boundary)]

            if "<=" in boundary and ":" in boundary:
                # ケース: "1000<=:1500>" -> [1000, 1500)
                start, end = nums[0], nums[1]
                parsed_intervals.append((start, end, postage))
                event_points.update([start, end])
            elif "<=" in boundary:
                # ケース: "0<=" -> [0, 無限)
                start = nums[0]
                parsed_intervals.append((start, float("inf"), postage))
                event_points.add(start)
            elif ">" in boundary:
                # ケース: "1000>" -> [0, 1000)
                end = nums[0]
                parsed_intervals.append((0, end, postage))
                event_points.add(end)

        # 2. 昇順に並べた境界値のリストを作成
        sorted_points = sorted(list(event_points))

        formatted_rules = []
        for i in range(len(sorted_points)):
            current_start = sorted_points[i]
            # この区間に適用される送料の合計を計算
            total_postage = 0

            # 各インターバルに対して、現在の地点(current_start)が含まれているか判定
            # (終了地点を含まない [start, end) の範囲で判定)
            for start, end, p in parsed_intervals:
                if start <= current_start < end:
                    total_postage += p

            formatted_rules.append((current_start, total_postage))

        # 3. 連続する区間で送料が同じ場合は整理（オプション）し、結果を格納
        # 最後の値が0（送料無料）になるケースも考慮されます
        shipping_rules[store] = formatted_rules

    return shipping_rules


def transform_shopping_data(data_list: list[dict]):
    item_names = set()
    store_prices = {}

    for entry in data_list:
        item = entry["itemname"]
        store = entry["storename"]
        price = int(entry["price"])

        # 商品名をセットに追加（重複排除）
        item_names.add(item)

        # 店舗が辞書になければ作成
        if store not in store_prices:
            store_prices[store] = {}

        # すでに価格がある場合は安い方を採用（重複データ対策）
        if item in store_prices[store]:
            if price < store_prices[store][item]:
                store_prices[store][item] = price
        else:
            store_prices[store][item] = price

    # 商品名をアルファベット順にソートしてリスト化
    sorted_items = sorted(list(item_names))

    return sorted_items, store_prices


def call_get_itemcomb_with_pulp(storeconf: dict, itemlist: list[dict]):
    items, prices = transform_shopping_data(itemlist)
    shipping_rules = convert_shipping_rules(storeconf)
    return get_itemcomb_with_pulp(prices, items, shipping_rules)


"""
prices = {
    '駿河屋': {'A': 1500,  'C': 1000,  'E': 1100, 'F': 1100, },
    # 省略
}
items = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
shipping_rules = {
    "静岡本店": [(0, 300)],
    "駿河屋": [
        (0, 440+240),     # 1000未満（1000>） , 5000円未満なので+240
        (1000, 385+240),   # 1000以上（1000<=）
        (1500, 240), # 1500以上
        (5000, 0)    # 5000以上
    ],
    # 省略
}
"""


def get_itemcomb_with_pulp(prices: dict, items: list, shipping_rules: dict):
    # 最小化問題
    prob = pulp.LpProblem("Best_Buy_Optimization", pulp.LpMinimize)

    # 1. 変数定義
    # buy[s][i]: 店舗sで商品iを買うか (その店舗に商品がある場合のみ作成)
    buy = pulp.LpVariable.dicts(
        "buy",
        [(s, i) for s in prices.keys() for i in items if i in prices[s]],
        cat="Binary",
    )

    # store_used[s]: 店舗sを利用するか
    store_used = pulp.LpVariable.dicts("store_used", prices.keys(), cat="Binary")

    # ship_rank[s, r]: 店舗sで送料ランクrを適用するか
    ship_rank = pulp.LpVariable.dicts(
        "ship_rank",
        [(s, r) for s in prices.keys() for r in range(len(shipping_rules[s]))],
        cat="Binary",
    )

    # 2. 制約条件
    # 各商品は必ずどこかの店舗（取り扱いがある店舗のみ）で1回だけ買う
    for item in items:
        valid_stores = [s for s in prices.keys() if item in prices[s]]
        if not valid_stores:
            continue  # 取り扱い店舗がない商品はスキップ（またはエラー処理）
        prob += pulp.lpSum([buy[(s, item)] for s in valid_stores]) == 1

    for s in prices.keys():
        # 取り扱いがある商品のリスト
        available_items = [i for i in items if i in prices[s]]

        # 商品を買うならその店舗を「使用中」にする
        for item in available_items:
            prob += buy[(s, item)] <= store_used[s]

        # 店舗合計金額の計算
        total_store_price = pulp.lpSum(
            [buy[(s, i)] * prices[s][i] for i in available_items]
        )

        # 送料ランクの選択：店舗を使うなら必ず1つ選択、使わないなら0
        prob += (
            pulp.lpSum([ship_rank[(s, r)] for r in range(len(shipping_rules[s]))])
            == store_used[s]
        )

        # 送料ランクのしきい値制約
        for r, (threshold, cost) in enumerate(shipping_rules[s]):
            # そのランクを選ぶなら、合計金額はしきい値(threshold)以上でなければならない
            # Mは十分大きな数（ここでは商品価格の合計などで代用可能だが、簡略化のためthresholdを使用）
            prob += total_store_price >= threshold * ship_rank[(s, r)]

    # 3. 目的関数
    total_item_cost = pulp.lpSum(
        [
            buy[(s, i)] * prices[s][i]
            for s in prices.keys()
            for i in items
            if i in prices[s]
        ]
    )
    total_shipping_cost = pulp.lpSum(
        [
            ship_rank[(s, r)] * shipping_rules[s][r][1]
            for s in prices.keys()
            for r in range(len(shipping_rules[s]))
        ]
    )

    # 目的関数：商品代 + 送料
    prob += total_item_cost + total_shipping_cost

    # 4. 解決
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    # 5. 結果表示
    results = {}
    grand_total_shipping = 0

    for s in prices.keys():
        # store_usedが1、かつ実際に商品が選択されているか確認
        if pulp.value(store_used[s]) > 0.5:
            available_items = [i for i in items if i in prices[s]]
            bought_items = [i for i in available_items if pulp.value(buy[(s, i)]) > 0.5]

            # 【修正点】実際に購入した商品がある場合のみ結果に追加
            if bought_items:
                subtotal = sum(prices[s][i] for i in bought_items)

                applied_shipping = 0
                for r in range(len(shipping_rules[s])):
                    if pulp.value(ship_rank[(s, r)]) > 0.5:
                        applied_shipping = shipping_rules[s][r][1]

                grand_total_shipping += applied_shipping

                results[s] = {
                    "items": [
                        {"itemname": name, "price": prices[s][name]}
                        for name in bought_items
                    ],
                    "sum_pos_out": subtotal,
                    "postage": applied_shipping,
                }

    results["sum_pos_in"] = pulp.value(prob.objective)
    results["sum_postage"] = grand_total_shipping
    return results


def getBoundaryInDict(d):
    BOUNDARY = "boundary"
    if BOUNDARY not in d or d[BOUNDARY] is None:
        return "0<="
    return d[BOUNDARY]


def getPostageInDict(d):
    POSTAGE = "postage"
    if POSTAGE not in d or d[POSTAGE] is None:
        return "0"
    return d[POSTAGE]


def createStoreConf(db: Session, itemidlist: list[int]):
    res = ItemQuery.get_current_storename_list_by_item_id(db, item_id_list=itemidlist)
    if res is None or len(res) == 0:
        return {}
    storenames: list[str] = [t for r in res for t in r]
    sp = StoreQuery.get_storepostage_by_storename(db, storenames=storenames)
    dicl = [dict(row._mapping.items()) for row in sp]
    storeconf = {}
    for d in dicl:
        if d["storename"] not in storeconf:
            storeconf[d["storename"]] = list()
        vald = {}
        vald["boundary"] = getBoundaryInDict(d)
        vald["postage"] = getPostageInDict(d)
        storeconf[d["storename"]].append(vald)
    return storeconf


def deleteLogger():
    logname = cmnlog.LogName.ITEMCOMB
    return cmnlog.deleteLogger(logname)


def getLogger():
    logname = cmnlog.LogName.ITEMCOMB
    return cmnlog.getLogger(logname)


def get_filename():
    return os.path.basename(__file__)


def startCalcSumitemComb(db: Session, itemidlist: list[int]):
    res = ItemQuery.get_latest_price_by_item_id_list(db, item_id_list=itemidlist)
    itemlist = [dict(row._mapping.items()) for row in res]
    storeconf = createStoreConf(db, itemidlist=itemidlist)
    logger = getLogger()
    logger.info(f"{get_filename()} searchcomb start")
    logger.info(f"{get_filename()} storeconf= {storeconf}")
    logger.info(f"{get_filename()} itemlist= {itemlist}")
    stime = time.perf_counter()
    ret = call_get_itemcomb_with_pulp(storeconf=storeconf, itemlist=itemlist)
    etime = time.perf_counter()
    ret["proc_time"] = etime - stime
    logger.info(get_filename() + " searchcomb end")
    return ret

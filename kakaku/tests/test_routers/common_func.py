from bs4 import BeautifulSoup
import common.util as cmn_util


def split_iteminfo_html(text):
    soup = BeautifulSoup(text, "html.parser", from_encoding="utf-8")
    table = soup.select(r".recent_table tr")
    results: dict = {}
    for tr in table:
        if not tr.has_attr("id"):
            continue
        td_list = tr.select(f"td")
        dic = {
            "item_id": int(td_list[0].text),
            "name": td_list[1].text,
            "url_id": int(td_list[2].text),
            "url": td_list[3].text,
            "newestprice": int(td_list[4].text),
            "trendrate": float(td_list[5].text),
            "salename": td_list[6].text,
            "storename": td_list[7].text,
            "created_at": cmn_util.dbtimeTodatetime(td_list[8].text),
            "lowestprice": int(td_list[9].text),
            "act": int(td_list[10].text),
        }
        results[dic["item_id"]] = dic
    return results

import sys
import re
import argparse
from typing import List, Dict, Set

from os.path import dirname

parent_dir = dirname(dirname(__file__))
sys.path.append(parent_dir)
from proc.scrapingmanage import sendTask
from proc.sendcmd import ScrOrder

from accessor.item import UrlQuery


def urlCheck(url):
    pattern = r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    if re.match(pattern, url):
        return True
    else:
        return False


def send_item_list(item_id_list: List[int]):
    item_id_url_list = [
        dict(ret._mapping.items()) for ret in UrlQuery.get_act_items_url()
    ]
    item_id_to_url_list: Dict[int, Set[str]] = {}
    for item_dic in item_id_url_list:
        if item_dic["item_id"] in item_id_to_url_list:
            item_id_to_url_list[item_dic["item_id"]].add(item_dic["urlpath"])
            continue
        else:
            item_id_to_url_list[item_dic["item_id"]] = set([item_dic["urlpath"]])
            continue
    for itemid in item_id_list:
        if itemid in item_id_to_url_list:
            for url in item_id_to_url_list[itemid]:
                if urlCheck(url):
                    print(f"sendtask url={url}, item_id={itemid}")
                    sendTask(ScrOrder.UPDATE, url, itemid)
                else:
                    print(f"NG url={url}, item_id={itemid}")
                continue


def send_url_list(url_list: List[str]):
    for url in url_list:
        if urlCheck(url):
            print(f"sendtask url={url}")
            sendTask(ScrOrder.UPDATE, url, -1)
        else:
            print(f"NG url={url}")


def param_parser(argv):
    parser = argparse.ArgumentParser(description="send task to scrapingmanage")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-u", "--url", metavar="urlpath", help="update url list", type=str, nargs="+"
    )
    group.add_argument(
        "-i",
        "--itemid",
        metavar="item_id",
        help="update item_id list",
        type=int,
        nargs="+",
    )
    group.add_argument("--urlall", help="update act all url", action="store_true")
    group.add_argument(
        "-do", "--db_organize", help="db organize", choices=["days", "sync"]
    )

    args = parser.parse_args(argv[1:])
    return args


def startcmd():
    param = param_parser(sys.argv)
    if param.url and len(param.url) > 0:
        print("start sendtask url")
        send_url_list(param.url)
        print("end sendtask url")
        return
    if param.itemid and len(param.itemid) > 0:
        print("start sendtask item")
        send_item_list(param.itemid)
        print("end sendtask item")
        return
    if param.urlall:
        print("start sendtask urlall")
        sendTask(ScrOrder.UPDATE_ACT_ALL, "", "")
        print("end sendtask urlall")
        return
    if param.db_organize:
        if param.db_organize == "days":
            print("start sendtask organize days")
            sendTask(ScrOrder.DB_ORGANIZE_DAYS, "", "")
            print("end sendtask organize days")
            return
        if param.db_organize == "sync":
            print("start sendtask organize sync")
            sendTask(ScrOrder.DB_ORGANIZE_SYNC, "", "")
            print("end sendtask organize sync")
            return
        print("no support param")
        return


def startcmd_old():
    argslen = len(sys.argv)
    if argslen < 2 or argslen > 3:
        print("ERROR PARAMETER_NUM")
        sys.exit()
    if ScrOrder.UPDATE_ACT_ALL == sys.argv[1]:
        sendTask(ScrOrder.UPDATE_ACT_ALL, "", "")
        return
    if urlCheck(sys.argv[1]):
        url = sys.argv[1]
    else:
        print("ERROR PARAMETER_URL")
        sys.exit()
    id = -1
    if argslen == 3:
        id = int(sys.argv[2])

    sendTask(ScrOrder.UPDATE, url, id)


if __name__ == "__main__":
    startcmd()

import sys

from os.path import dirname

parent_dir = dirname(dirname(__file__))
sys.path.append(parent_dir)
from accessor.item import UrlQuery, ItemQuery
from accessor.item.item import OrganizerQuery


def create_pricelog_2days(start_url_id: int = 0):
    ob = get_url_list()
    shintyoku_num = 10
    cnt = 0
    for url in ob:
        if start_url_id > url.url_id:
            continue
        pricelog_list = OrganizerQuery.get_recent_pricelog_by_url_id(url.url_id)
        for row in pricelog_list:
            pl_dict = {k: v for k, v in row._mapping.items()}
            ItemQuery.add_pricelog_2days_by_dict(pldict=pl_dict)
        cnt += 1
        if cnt % shintyoku_num == 0:
            print(f"yomitori count={cnt}, url_id={url.url_id}")


def get_url_list():
    url_list = UrlQuery.get_url_all()
    for url in url_list:
        yield url


def main(argv):
    start_url_id = 0
    if len(argv) > 1:
        start_url_id = int(argv[1])
    print("start create pricelog_2days")
    create_pricelog_2days(start_url_id=start_url_id)
    print("end create pricelog_2days")


if __name__ == "__main__":
    main(sys.argv)

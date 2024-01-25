import os
import sys

from os.path import dirname

parent_dir = dirname(dirname(__file__))
sys.path.append(parent_dir)

from accessor.item import UrlQuery, NewestQuery
from accessor.item.item import OldItemQuery
from accessor.read_sqlalchemy import get_session, get_old_db_session


def delete_all_related_by_url(url: str):
    with next(get_session()) as db:
        url_id = UrlQuery.get_url_id_by_url(db, url=url)
        if not url_id:
            print("not found url")
            return
        UrlQuery.delete_all_related_by_url(db=db, url_id=url_id)
        NewestQuery.update_by_deleting_url(db=db, url_id=url_id)
    with next(get_old_db_session()) as db:
        OldItemQuery.delete_pricelog_by_url(db, url_id=url_id)


def main(argv):
    if len(argv) != 2 or not argv[1]:
        print(f"Not enough arguments. {os.path.basename(__file__)} [url] ")
        return
    print(f"Are you sure you want to delete the URL ({argv[1]})")
    yesno = input("yes or no > ").lower()
    if yesno not in ["y", "ye", "yes"]:
        print("not delete end")
        return
    print("delete start")
    delete_all_related_by_url(argv[1])
    print("delete end")


if __name__ == "__main__":
    main(sys.argv)

import os
import sys

from os.path import dirname

parent_dir = dirname(dirname(__file__))
sys.path.append(parent_dir)


from sqlalchemy import (
    update,
    func,
)
from sqlalchemy.orm import Session

from model.item import Url
from accessor.read_sqlalchemy import get_session

target_domain = "www.netoff.co.jp"


def convert_db_url(db: Session):
    stmt = (
        update(Url)
        .where(Url.urlpath.contains(target_domain))
        .where(Url.urlpath.not_like("%/"))
        .values(urlpath=Url.urlpath + "/")
    )
    db.execute(stmt)
    db.commit()


def main():
    print("start update netoff url")

    with next(get_session()) as db:
        convert_db_url(db=db)
    print("end update netoff url")


if __name__ == "__main__":
    main()

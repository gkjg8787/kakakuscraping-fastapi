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

from model.item import (
    Url
)
from accessor.read_sqlalchemy import get_session

target_domain = "www.suruga-ya.jp"
source_word = "product-other"
converted_word = "product/other"


def convert_db_url(db :Session,
                   domain :str,
                   src :str,
                   conv :str):
    stmt = ( update(Url)
            .where(Url.urlpath.contains(domain))
            .where(Url.urlpath.contains(src))
            .values(urlpath=func.replace(Url.urlpath, src, conv))
            )
    db.execute(stmt)
    db.commit()

def main(argv):
    if len(argv) < 4 and len(argv) > 1:
        print(f"Not enough arguments. {os.path.basename(__file__)} [domain] [source string] [converted string]")
        return
    print("start update db url")
    if len(argv) == 1:
        domain = target_domain
        src = source_word
        conv = converted_word
    else:
        domain = argv[1]
        src = argv[2]
        conv = argv[3]
    print(f'domain={domain}, src={src}, conv={conv}')
    res = None
    with next(get_session()) as db:
        convert_db_url(db=db, domain=domain, src=src, conv=conv)
    print("end update db url")

if __name__ == '__main__':
    main(sys.argv)
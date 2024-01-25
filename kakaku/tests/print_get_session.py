from accessor.read_sqlalchemy import get_session
from tests.test_db import test_db


def test_get_session(db):
    print("--- start test_get_session ---")
    configs = db.connection().engine.url.translate_connect_args()
    dbi = db.connection().dialect.name
    print(f"configs={configs}")
    print(f"dbi={dbi}")
    print("--- end test_get_session ---")


def main(db=next(get_session())):
    test_get_session(db)
    test_get_session(db)
    test_get_session(db)


if __name__ == "__main__":
    main()

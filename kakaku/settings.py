from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASES = {
    "default": {
        "drivername": "sqlite",
        "database": f"{BASE_DIR}/db/iteminfo.sqlite",
    },
    "old_db": {
        "drivername": "sqlite",
        "database": f"{BASE_DIR}/db/iteminfo_old.sqlite",
    },
    "postgre_default": {
        "drivername": "postgresql+psycopg2",
        "username": "dbuser",
        "password": "posgre134",
        "host": "postgres",
        "database": "appdb",
        "port": "5432",
    },
    "postgre_old_db": {
        "drivername": "postgresql+psycopg2",
        "username": "dbuser",
        "password": "posgre134",
        "host": "postgres",
        "database": "olddb",
        "port": "5432",
    },
    "is_echo": False,
}

HTMLTEMP = f"{BASE_DIR}/tempdata/html/"
LOGTEMP = f"{BASE_DIR}/tempdata/log/"
SEARCHOPTION_DIR = f"/{SRC_DIR}/url_search/"

SEARCHOPTIONS_DEFAULT = {
    "ZAIKO": {"INIT": "OFF"},
    "SAFES": {
        "DISPLAY": "OFF",
        "INIT": "ON",
    },
    "LISTVIEW": {"INIT": "OFF"},
    "CATEGORY": {"VALUE": "全て"},
    "STORE": {
        "駿河屋": "OFF",
        "ブックオフ": "OFF",
        "ネットオフ": "OFF",
    },
}

DB_VERSION = (0, 1, 0)
SYSTEM_STATUS_LOG_MAX = 50

AUTO_DEL_DLFILE = True
NO_VERIFY_DOMAIN = ""  # "www.netoff.co.jp"
ITEMCOMB_SELECT_LIMIT = 7
SEARCH_CACHE = True
CACHE_TIME = 60
CACHE_MAX_NUM = 5

SUPPORT_DOMAIN = {
    "surugaya": "www.suruga-ya.jp",
    "netoff": "www.netoff.co.jp",
    "bookoff": "shopping.bookoff.co.jp",
}

SCRAPING_BACK_SERVER = {
    "addr": "127.0.0.1",
    "port": "5000",
}

PROC_QUEUE_TIMEOUT = 3
EXE_ITEMCOMB = "bin"
AUTO_UPDATE_ITEM = False
AUTO_UPDATE_TIME = ["16:16"]
AUTO_UPDATE_CHECK_CYCLE_TIME = 5
AUTO_DB_ORGANIZER_CYCLE_TIME = 600
AUTO_UPDATE_ONLINE_STORE = False
AUTO_UPDATE_ONLINE_STORE_TIME = ["16:40"]
AUTO_UPDATE_ONLINE_STORE_CYCLE_TIME = 600
DEFAULT_SHIPPING_PREFECTURE = "東京都"
AUTO_COPY_OF_ONLINE_STORE_INFO_TO_LOCAL = {"auto": False, "type": "overwrite"}
AUTO_STARTUP_BACKSERVER = {"auto": False}
ITEMCOMB_PRICE_MARGIN = {"type": "fix", "value": "250", "min-value": "250"}
SURUGAYA_SEARCH_RESULT_URL_CONVERT = True
PREDICTION = {
    "view": True,
    "everytime": False,
    "forecast_length": 14,
    "show_accuracy": False,
    "learning_timeout": 10,
}
ITEM_PARSE_OPTIONS = {
    "surugaya": {
        "get_other_items_in_detail_page": False,
    },
    "excluded_condition_keywords": [],  # ["難", "欠", "ランクB", "不備", "ディスクのみ"]
}
ALLOW_UNSUPPORTED_LINKS_IN_HTML = False
API_OPTIONS = {
    "enable": False,
    "excluded_condition_keywords": [],
    "skip_zero_price": True,
}
OPERATION_MENU_OPTIONS = {
    "add_links": {
        "enabled": False,
        "links": [
            {"enabled": True, "name": "search_gui", "url": "http://localhost:8110/"},
        ],
    }
}

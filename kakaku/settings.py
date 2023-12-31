
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASES = {
    "default":{
        "drivername":"sqlite",
        "database":f"{BASE_DIR}/db/iteminfo.sqlite",
    },
    "old_db":{
        "drivername":"sqlite",
        "database":f"{BASE_DIR}/db/iteminfo_old.sqlite",
    },
    "postgre_default":{
        "drivername":"postgresql+psycopg2",
        "username":"dbuser",
        "password":"posgre134",
        "host":"postgres",
        "database":"appdb",
        "port":"5432",
    },
    "postgre_old_db":{
        "drivername":"postgresql+psycopg2",
        "username":"dbuser",
        "password":"posgre134",
        "host":"postgres",
        "database":"olddb",
        "port":"5432",
    },
    "is_echo":False
}
HTMLTEMP=f"{BASE_DIR}/tempdata/html/"
LOGTEMP=f"{BASE_DIR}/tempdata/log/"

SEARCHOPTION=f"/{SRC_DIR}/url_search/"

DB_VERSION=(0, 1, 0)
SYSTEM_STATUS_LOG_MAX=20

AUTO_DEL_DLFILE=True
NO_VERIFY_DOMAIN="" #"www.netoff.co.jp"
ITEMCOMB_SELECT_LIMIT=7
SEARCH_CACHE=True
CACHE_TIME=60
CACHE_MAX_NUM=5

SUPPORT_DOMAIN = {
    'surugaya':'www.suruga-ya.jp',
    'netoff':'www.netoff.co.jp',
    'bookoff':'shopping.bookoff.co.jp',
    'geo':'ec.geo-online.co.jp',
}

SCRAPING_BACK_SERVER = {
    "addr":"127.0.0.1",
    "port":"5000",
}
PROC_QUEUE_TIMEOUT = 5
EXE_ITEMCOMB = "bin"
AUTO_UPDATE_ITEM = False
AUTO_UPDATE_TIME = ["16:16"]


from pathlib import Path

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
    "postgresql":{
        "drivername":"postgresql+pg8000",
        "username":"dbuser",
        "password":"kx@jj5/g",
        "host":"pghost10",
        "database":"appdb",
        "port":"6400",
    },
    "is_echo":False
}
HTMLTEMP=f"{BASE_DIR}/tempdata/html/"
LOGTEMP=f"{BASE_DIR}/tempdata/log/"

SEARCHOPTION=f"/{Path(__file__).resolve().parent}/url_search/"
ITEMCOMBOPTION="/scraping/ctrl/itemcomb/"

AUTO_DEL_DLFILE=True
NO_VERIFY_DOMAIN="" #"www.netoff.co.jp"
ITEMCOMB_SELECT_LIMIT=4
SEARCH_CACHE=True
CACHE_TIME=60
CACHE_MAX_NUM=5

SUPPORT_DOMAIN = [
    'www.suruga-ya.jp',
    'www.netoff.co.jp',
    'www.bookoffonline.co.jp',
    'ec.geo-online.co.jp',
]

SCRAPING_BACK_SERVER = {
    "addr":"127.0.0.1",
    "port":"5000",
}
PROC_QUEUE_TIMEOUT = 5
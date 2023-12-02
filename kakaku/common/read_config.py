import settings


def get_srcdir():
    return settings.SRC_DIR

def get_databases():
    return settings.DATABASES

def get_support_url():
    return settings.SUPPORT_DOMAIN

def get_log_dir():
    return settings.LOGTEMP

def get_dl_temp_dir():
    return settings.HTMLTEMP

def get_cache_max_num():
    return settings.CACHE_MAX_NUM

def get_cache_time():
    return settings.CACHE_TIME

def is_search_cache():
    return settings.SEARCH_CACHE

def get_no_verify_domain():
    return settings.NO_VERIFY_DOMAIN

def is_auto_del_dl_file():
    return settings.AUTO_DEL_DLFILE

def get_back_server_config():
    return settings.SCRAPING_BACK_SERVER

def get_back_server_queue_timeout():
    return settings.PROC_QUEUE_TIMEOUT

def get_search_option_path():
    return settings.SEARCHOPTION

def get_itemcomb_select_limit():
    return settings.ITEMCOMB_SELECT_LIMIT

def get_exec_itemcomb():
    return settings.EXE_ITEMCOMB

def is_auto_update_item():
    return settings.AUTO_UPDATE_ITEM

def get_auto_update_time():
    return settings.AUTO_UPDATE_TIME

def get_db_version():
    return settings.DB_VERSION

def get_system_status_log_max():
    return settings.SYSTEM_STATUS_LOG_MAX
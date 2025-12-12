from typing import Annotated
from annotated_types import Gt
from pydantic import BaseModel, Field

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
    return settings.SEARCHOPTION_DIR


def get_search_options_default():
    return settings.SEARCHOPTIONS_DEFAULT


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


def get_auto_update_check_cycle_time():
    return settings.AUTO_UPDATE_CHECK_CYCLE_TIME


def get_auto_db_organizer_check_cycle_time():
    return settings.AUTO_DB_ORGANIZER_CYCLE_TIME


def is_auto_update_online_store():
    return settings.AUTO_UPDATE_ONLINE_STORE


def get_auto_update_online_store_time():
    return settings.AUTO_UPDATE_ONLINE_STORE_TIME


def get_auto_update_online_store_cycle_time():
    return settings.AUTO_UPDATE_ONLINE_STORE_CYCLE_TIME


def get_default_shipping_prefecture_name():
    return settings.DEFAULT_SHIPPING_PREFECTURE


def get_auto_startup_backserver():
    return settings.AUTO_STARTUP_BACKSERVER


def get_itemcomb_price_margin():
    return settings.ITEMCOMB_PRICE_MARGIN


def get_auto_copy_of_online_store_info_to_local():
    return settings.AUTO_COPY_OF_ONLINE_STORE_INFO_TO_LOCAL


def get_surugaya_search_result_url_convert():
    return settings.SURUGAYA_SEARCH_RESULT_URL_CONVERT


class PredictionConfig(BaseModel):
    view: bool
    everytime: bool
    forecast_length: Annotated[int, Gt(0)]
    show_accuracy: bool
    learning_timeout: Annotated[int, Gt(0)]


def get_prediction_setting():
    return PredictionConfig(**settings.PREDICTION)


class SurugayaParseOptions(BaseModel):
    get_other_items_in_detail_page: bool


class ItemParseOptions(BaseModel):
    surugaya: SurugayaParseOptions
    excluded_condition_keywords: list[str]


def get_item_parse_options():
    return ItemParseOptions(**settings.ITEM_PARSE_OPTIONS)


def get_allow_unsupported_links_in_html():
    return settings.ALLOW_UNSUPPORTED_LINKS_IN_HTML


class APIOptions(BaseModel):
    enable: bool
    excluded_condition_keywords: list[str] = Field(default_factory=list)
    skip_zero_price: bool = True


def get_api_options():
    return APIOptions(**settings.API_OPTIONS)


class LinkItem(BaseModel):
    enabled: bool
    name: str
    url: str


class AddLinksOptions(BaseModel):
    enabled: bool
    links: list[LinkItem]


class OperationMenuOptions(BaseModel):
    add_links: AddLinksOptions


def get_operation_menu_options():
    return OperationMenuOptions(**settings.OPERATION_MENU_OPTIONS)

from datetime import datetime

from pydantic import BaseModel, Field

from common import const_value


class ParseInfo(BaseModel):
    url: str = ""
    name: str = ""
    price: int = const_value.INIT_PRICE
    condition: str = ""
    taxin: bool = False
    on_sale: bool = False
    salename: str = ""
    timestamp: datetime | None = None
    is_success: bool = False
    storename: str = ""


class ParseInfos(BaseModel):
    infos: list[ParseInfo] = Field(default_factory=list)


class ParseInfosUpdate(ParseInfos):
    pass


class DBParseInfo(ParseInfo):
    url_id: int


class ParseInfosUpdateResponse(BaseModel):
    infos: list[DBParseInfo] = Field(default_factory=list)


class PriceUpdateResponse(BaseModel):
    ok: bool
    error_msg: str


class Item(BaseModel):
    name: str


class ItemCreate(Item):
    urls: list[str] = Field(..., min_length=1)


class DBItem(Item):
    item_id: int | None


class ItemCreateResponse(DBItem):
    pass


class URLActive(BaseModel):
    url: str
    is_active: bool = False


class ItemToURL(BaseModel):
    item_id: int
    url_actives: list[URLActive] = Field(default_factory=list)


class ItemUpdate(ItemToURL):
    name: str | None = None


class ItemUpdateResponse(ItemUpdate):
    pass


class ItemsURLCreate(ItemToURL):
    pass


class DBURLActive(URLActive):
    url_id: int


class DBItemToURL(BaseModel):
    item_id: int
    url_actives: list[DBURLActive] = Field(default_factory=list)


class ItemsURLCreateResponse(DBItemToURL):
    pass


class URLtoItemGet(BaseModel):
    url: str


class DBURLtoItem(BaseModel):
    url_active: DBURLActive
    items: list[DBItem] = Field(default_factory=list)


class URLtoItemGetResponse(DBURLtoItem):
    pass


class ActItem(DBItem):
    act: int = 0


class RedirectOptions(BaseModel):
    stop_on_redirect: bool = False
    ignore_trailing_slash: bool = True
    ignore_add_query: bool = True


class AskGeminiOptions(BaseModel, extra="ignore"):
    sitename: str = ""
    label: str = ""
    redirect_options: RedirectOptions | None = None


class SearchRequest(BaseModel):
    url: str | None = Field(default=None)
    search_keyword: str | None = Field(default=None)
    sitename: str
    options: AskGeminiOptions | dict = Field(default_factory=dict)
    no_cache: bool = Field(default=False)


class DownloadRequest(BaseModel):
    url: str
    sitename: str
    options: AskGeminiOptions | dict = Field(default_factory=dict)
    no_cache: bool = Field(default=False)


class ParserRequest(BaseModel):
    html: str
    url: str | None = None
    options: AskGeminiOptions | dict | None = Field(default=None)


class UrlGenerationResponse(BaseModel):
    url: str


class DownloadResponse(BaseModel):
    html: str
    redirect_url: str | None = None
    download_type: str | None = None


class SearchResult(BaseModel):
    title: str | None = None
    price: int | None = None
    taxin: bool = False
    condition: str | None = None
    on_sale: bool = False
    salename: str | None = None
    is_success: bool = False
    url: str | None = None
    sitename: str | None = None
    image_url: str | None = None
    stock_msg: str | None = None
    stock_quantity: int | None = None
    sub_urls: list[str] | None = Field(default=None)
    shops_with_stock: str | None = None
    others: dict | None = Field(default=None)


class SearchResults(BaseModel):
    results: list[SearchResult] = Field(default_factory=list)
    error_msg: str = Field(default="")
    redirect_url: str | None = None

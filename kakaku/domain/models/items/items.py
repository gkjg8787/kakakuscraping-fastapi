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

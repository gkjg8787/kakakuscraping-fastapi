import os

from sqlalchemy import (
    select,
)
from model.item import (
    Item as db_Item,
    Url as db_URL,
    UrlInItem as db_URLinItem,
)

from accessor.read_sqlalchemy import Session
from domain.models.items import repository, items as m_items
from .item.item import NewestQuery, UrlQuery, UrlActive, ItemQuery
from html_parser import htmlparse, api_model
from common import const_value, cmnlog
from proc.scrapingmanage import sendTask
from proc.sendcmd import ScrOrder
from proc import get_sys_status, system_status


class ItemCreateRepository(repository.IItemCreateRepository):
    db: Session

    def __init__(self, db: Session):
        self.db = db

    def save(self, item: m_items.ItemCreate):
        item_id = NewestQuery.add_item(
            db=self.db, item_name=item.name, url_path=item.urls[0]
        )
        if len(item.urls) < 2:
            return m_items.ItemCreateResponse(**item.model_dump(), item_id=item_id)
        else:
            for url in item.urls[1:]:
                UrlQuery.add_url_and_urlinitem(db=self.db, urlpath=url, item_id=item_id)
            return m_items.ItemCreateResponse(**item.model_dump(), item_id=item_id)


class ItemUpdateRepository(repository.IItemUpdateRepository):
    db: Session

    def __init__(self, db: Session):
        self.db = db

    def save(self, item: m_items.ItemUpdate):
        db_item = ItemQuery.get_item(db=self.db, item_id=item.item_id)
        if not db_item:
            raise ValueError("Not Found item_id")
        if item.name is not None:
            ItemQuery.update_items_name_by_item_id(
                db=self.db, item_id=item.item_id, name=item.name
            )
        for urlact in item.url_actives:
            db_url = UrlQuery.get_url(db=self.db, urlpath=urlact.url)
            if not db_url:
                continue
            else:
                url_id = db_url.url_id
            if urlact.is_active:
                act_val = UrlActive.ACTIVE
            else:
                act_val = UrlActive.INACTIVE
            UrlQuery.update_url_active(
                db=self.db, item_id=item.item_id, url_id=url_id, isactive=act_val
            )
        return m_items.ItemUpdateResponse(**item.model_dump())


class ItemsURLCreateRepository(repository.IItemsURLCreateRepository):
    db: Session

    def __init__(self, db: Session):
        self.db = db

    def save(self, item: m_items.ItemsURLCreate):
        db_item = ItemQuery.get_item(db=self.db, item_id=item.item_id)
        if not db_item:
            raise ValueError("Not Found item_id")
        response = m_items.ItemsURLCreateResponse(item_id=item.item_id)
        for urlact in item.url_actives:
            db_url = UrlQuery.get_url(db=self.db, urlpath=urlact.url)
            if db_url:
                response.url_actives.append(
                    m_items.DBURLActive(
                        url=urlact.url, is_active=urlact.is_active, url_id=db_url.url_id
                    )
                )
                continue
            url_id = UrlQuery.add_url_and_urlinitem(
                db=self.db, urlpath=urlact.url, item_id=item.item_id
            )
            if not urlact.is_active:
                UrlQuery.update_url_active(
                    db=self.db,
                    item_id=item.item_id,
                    url_id=url_id,
                    isactive=UrlActive.INACTIVE,
                )
            response.url_actives.append(
                m_items.DBURLActive(
                    url=urlact.url, is_active=urlact.is_active, url_id=url_id
                )
            )
        return response


class NotifyPriceUpdateRepository(repository.IPriceUpdateRepository):
    db: Session

    def __init__(self, db: Session):
        self.db = db

    def save(self, parseinfos: m_items.ParseInfosUpdate):
        logger = cmnlog.getLogger(cmnlog.LogName.API)
        logger_header = os.path.basename(__file__)
        syssts = get_sys_status.getSystemStatus(self.db)
        if (
            syssts == system_status.SystemStatus.NONE.name
            or syssts == system_status.SystemStatus.FAULT.name
            or syssts == system_status.SystemStatus.STOP.name
        ):
            errmsg = f"{logger_header} unable to update server status = {syssts}"
            logger.warning(errmsg)
            return m_items.PriceUpdateResponse(ok=False, error_msg=errmsg)
        parseitems_dict = self._convert_parseinfos_to_parseitems(
            parseinfos=parseinfos, logger=logger, logheader=logger_header
        )
        if not parseitems_dict:
            errmsg = f"{logger_header} no data, no update"
            logger.info(errmsg)
            return m_items.PriceUpdateResponse(ok=False, error_msg=errmsg)
        logger.info(
            f"{logger_header} update via api start target_url_id={list(parseitems_dict.keys())}"
        )
        sendTask(cmdstr=ScrOrder.UPDATE_API_PRICE, data=parseitems_dict)
        logger.debug(f"{logger_header} update via api end")
        return m_items.PriceUpdateResponse(ok=True, error_msg="")

    def _convert_parseinfos_to_parseitems(
        self, parseinfos: m_items.ParseInfosUpdate, logger, logheader: str
    ):
        results: dict[int, api_model.ParseItemsForPriceUpdate] = {}
        for parseinfo in parseinfos.infos:
            url_id = UrlQuery.get_url_id_by_url(db=self.db, url=parseinfo.url)
            if url_id is None:
                errmsg = f"{logheader} URL is not registered, url:{parseinfo.url}"
                logger.warning(errmsg)
                continue
            new_price = const_value.INIT_PRICE
            used_price = const_value.INIT_PRICE
            if "新品" in parseinfo.condition:
                new_price = parseinfo.price
            else:
                used_price = parseinfo.price
            pii = htmlparse.ParseItemInfo(
                id=url_id,
                name=parseinfo.name,
                newPrice=new_price,
                usedPrice=used_price,
                condition=parseinfo.condition,
                taxin=parseinfo.taxin,
                onSale=parseinfo.on_sale,
                saleName=parseinfo.salename,
                timeStamp=parseinfo.timestamp,
                isSuccess=parseinfo.is_success,
                url=parseinfo.url,
                storename=parseinfo.storename,
            )
            if url_id in results.keys():
                results[url_id].add_parseiteminfo(pii)
            else:
                results[url_id] = api_model.ParseItemsForPriceUpdate(
                    parseiteminfos=[pii]
                )
        return results


class UnRegisteredURLError(Exception):
    pass


class UnRegisteredItemError(Exception):
    pass


class URLtoItemsRepository(repository.IURLtoItemsRepository):
    db: Session

    def __init__(self, db: Session):
        self.db = db

    def get(self, url: str):
        if not url:
            raise ValueError(f"url is None")
        results = self._get_db_url_to_item(db=self.db, url=url)
        if not results:
            db_url = UrlQuery.get_url(db=self.db, urlpath=url)
            if not db_url:
                raise UnRegisteredURLError("URL is not registered")
            raise UnRegisteredItemError("URL is not registered in item")
        return self._convert_db_to_response(results=results)

    def _convert_db_to_response(self, results) -> m_items.URLtoItemGetResponse | None:
        items: list[m_items.DBItem] = []
        urls: list[m_items.DBURLActive] = []
        urls_hash: set[str] = set()
        for result in results:
            item = result[0]
            if not isinstance(item, db_Item):
                raise ValueError(f"not db_item object, item:{item}")
            items.append(m_items.DBItem(item_id=item.item_id, name=item.name))
            url = result[1]
            urlinitem = result[2]
            if not isinstance(url, db_URL) or not isinstance(urlinitem, db_URLinItem):
                raise ValueError(
                    f"not db_url or not db_urlinitem, url:{url}, urlinitem:{urlinitem}"
                )
            if urlinitem.active == UrlActive.ACTIVE.value:
                is_active = True
            else:
                is_active = False
            url_active = m_items.DBURLActive(
                url=url.urlpath, url_id=url.url_id, is_active=is_active
            )
            urls.append(url_active)
            if url_active.model_dump_json() in urls_hash:
                continue
            elif len(urls_hash) > 0:
                raise ValueError(
                    f"There are multiple URLs , urls_hash{urls_hash}, new_url_active:{url_active}"
                )
            urls_hash.add(url_active.model_dump_json())

        return m_items.URLtoItemGetResponse(url_active=urls[0], items=items)

    def _get_db_url_to_item(self, db: Session, url: str):
        stmt = (
            select(db_Item, db_URL, db_URLinItem)
            .select_from(db_URL)
            .join(
                db_URLinItem,
                db_URLinItem.url_id == db_URL.url_id,
            )
            .join(db_Item, db_Item.item_id == db_URLinItem.item_id)
            .where(db_URL.urlpath == url)
        )
        result = db.execute(stmt)
        return result.all()

import os

from domain.models.items import repository, items as m_items
from .item.item import NewestQuery, UrlQuery, UrlActive, ItemQuery
from html_parser import htmlparse, api_model
from common import const_value, cmnlog
from proc.scrapingmanage import sendTask
from proc.sendcmd import ScrOrder
from proc import get_sys_status, system_status


class ItemCreateRepository(repository.IItemCreateRepository):

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


class PriceUpdateRepository(repository.IPriceUpdateRepository):

    def save(self, parseinfos: m_items.ParseInfosUpdate):
        parseitems_dict = self._convert_parseinfos_to_parseitems(parseinfos=parseinfos)
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

    def _convert_parseinfos_to_parseitems(self, parseinfos: m_items.ParseInfosUpdate):
        results: dict[int, api_model.ParseItemsForPriceUpdate] = {}
        # update_response = m_items.ParseInfosUpdateResponse()
        for parseinfo in parseinfos.infos:
            url_id = UrlQuery.get_url_id_by_url(db=self.db, url=parseinfo.url)
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
            """
            update_response.infos.append(
                m_items.DBParseInfo(**parseinfo.model_dump(), url_id=url_id)
            )
            """
        # return results, update_response
        return results

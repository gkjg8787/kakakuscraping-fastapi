from datetime import datetime, timezone
import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session


from accessor.read_sqlalchemy import get_session
from domain.models.items import items
from accessor import api
from common import read_config, filter_name
from html_parser.surugaya_html_parse import SurugayaParse
from html_parser.surugaya_search import SearchSurugaya
from url_search import readoption
from url_search.surugaya.surugayaURL import SurugayaURL
from url_search.surugaya.surugayaSearchOpt import SurugayaSearchOpt
import parameter_parser.item as ppi
from downloader import download_html as dl

router = APIRouter(prefix="/api", tags=["api"])


@router.post(
    "/items/",
    response_model=items.ItemCreateResponse,
    description="アイテムを新規作成します。",
)
def api_add_item(
    item: items.ItemCreate,
    db: Session = Depends(get_session),
):
    repo = api.ItemCreateRepository(db=db)
    response = repo.save(item)
    return response


@router.get(
    "/items/",
    response_model=List[items.ActItem],
    description="アイテム一覧を取得します。",
)
def api_get_items(
    filter_query: ppi.NewestFilterQuery = Depends(),
    db: Session = Depends(get_session),
):
    repo = api.ItemGetRepository(db=db)
    response = repo.get(filter=filter_query.get_filter_dict())
    return response


@router.patch(
    "/items/",
    response_model=items.ItemUpdateResponse,
    description="登録済みのアイテムの名前、URL状態を更新します。未登録のものは更新しません。",
)
def api_update_item(
    item: items.ItemUpdate,
    db: Session = Depends(get_session),
):
    repo = api.ItemUpdateRepository(db=db)
    try:
        response = repo.save(item)
    except ValueError as e:
        raise HTTPException(status_code=404)
    return response


@router.post(
    "/items/urls/",
    response_model=items.ItemsURLCreateResponse,
    description="対象のアイテムにURLを追加します。アイテムに登録済みのURLは更新しません。",
)
def api_add_items_url(
    item: items.ItemsURLCreate,
    db: Session = Depends(get_session),
):
    repo = api.ItemsURLCreateRepository(db=db)
    try:
        response = repo.save(item)
    except ValueError as e:
        raise HTTPException(status_code=404)
    return response


@router.get(
    "/urls/items/",
    response_model=items.URLtoItemGetResponse,
    description="対象のURLが登録されているアイテムの一覧を取得します。",
)
def api_get_url_to_items(
    url: str = Query(..., description="Target URL to process"),
    db: Session = Depends(get_session),
):
    if not url:
        raise HTTPException(status_code=404, detail="invalid URL. No length.")
    repo = api.URLtoItemsRepository(db=db)
    try:
        response = repo.get(url=url)
    except api.UnRegisteredURLError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except api.UnRegisteredItemError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return response


@router.patch(
    "/price/",
    response_model=items.PriceUpdateResponse,
    description="登録されたURLの価格情報を登録します。",
)
def api_update_price(
    parseinfos: items.ParseInfosUpdate, db: Session = Depends(get_session)
):
    repo = api.NotifyPriceUpdateRepository(db=db)
    response = repo.save(parseinfos=parseinfos)
    return response


@router.post(
    "/ex_search/url_generation/",
    response_model=items.UrlGenerationResponse,
    description="指定されたキーワードとサイト名から検索URLを生成します。",
)
def api_ex_search_url_generation(
    search_request: items.SearchRequest,
):
    s_url = SurugayaURL(readoption.ReadSearchOpt())
    if search_request.search_keyword:
        s_url.setWord(word=search_request.search_keyword)

    # options から category を取得 (dict または Pydantic モデルの両方に対応)
    opts = search_request.options
    category = None
    if isinstance(opts, dict):
        category = opts.get("category")

    if category:
        s_url.setParameter(param={"category": category})

    return items.UrlGenerationResponse(url=s_url.createURL())


@router.post(
    "/ex_search/download/",
    response_model=items.DownloadResponse,
    description="指定されたURLのHTMLコンテンツをダウンロードします。",
)
def api_ex_search_download(
    download_request: items.DownloadRequest,
):
    sod = read_config.get_search_options_default()
    param = {}
    for key in sod:
        if key.lower() == filter_name.FilterQueryName.SAFES.value:
            if "INIT" in sod[key] and sod[key]["INIT"] == "OFF":
                param[filter_name.FilterQueryName.SAFES.value] = 0
            else:
                param[filter_name.FilterQueryName.SAFES.value] = 1
    sso = SurugayaSearchOpt(readoption.ReadSearchOpt())
    sso.setParamOpt(param)
    success, html_text = dl.getUrlHtml(url=download_request.url, opt=sso.requestOpt)
    if not success:
        return items.DownloadResponse(html="", redirect_url=None, download_type=None)

    return items.DownloadResponse(
        html=html_text,
        redirect_url=None,
        download_type=None,
    )


@router.post(
    "/ex_search/parser/",
    response_model=items.SearchResults,
    description="ダウンロードされたHTMLを解析し、商品情報を抽出します。",
)
def api_ex_search_parser(
    parser_request: items.ParserRequest,
):
    url = parser_request.url or ""
    html = parser_request.html
    parsed_items = []

    if "/product/" in url:
        # 商品詳細ページの解析
        ipopts = read_config.get_item_parse_options()
        p = SurugayaParse(
            fp=html,
            id=0,
            date=datetime.now(timezone.utc),
            url=url,
            itemparseoptions=ipopts,
        )
        parsed_items = p.getItems()
        results = [
            items.SearchResult(
                title=item.name,
                price=item.getLowestPrice() if item.getLowestPrice() >= 0 else None,
                taxin=item.taxin,
                condition=item.condition,
                on_sale=item.onSale,
                salename=item.saleName,
                is_success=item.isSuccess,
                url=item.url,
                sitename=item.storename,
                stock_quantity=item.stockQuantity,
            )
            for item in parsed_items
        ]
    elif "search?" in url:
        # 検索結果ページの解析
        s = SearchSurugaya(
            is_converturl=read_config.get_surugaya_search_result_url_convert() or False
        )
        s.parseSearch(htmltext=html)
        parsed_items = s.getItems()
        results = []

        def get_min_price(text):
            match = re.search(r"[\d,]+", text)
            if match:
                return int(match.group().replace(",", ""))
            return None

        for item in parsed_items:
            result = items.SearchResult(
                title=item.get(s.TITLE),
                is_success=True,
                url=url or item.get(s.TITLE_URL),
                sitename=item.get(s.STORENAME),
                image_url=item.get(s.IMAGE_URL),
            )

            if item.get(s.MAKEPURE):
                makepure = items.SearchResult(**result.model_dump())

            try:
                if item.get(s.USED):
                    result.price = get_min_price(item.get(s.USED))
                    result.taxin = True
                    result.condition = "中古"
                elif item.get(s.NEW):
                    result.price = get_min_price(item.get(s.NEW))
                    result.taxin = True
                    result.condition = "新品"
                elif item.get(s.SINAGIRE):
                    result.price = None
                    result.stock_msg = "品切れ"
            except ValueError:
                result.price = None

            if item.get(s.TITLE_URL):
                result.sub_urls = (
                    [item.get(s.TITLE_URL)] if item.get(s.TITLE_URL) else None
                )
            if item.get(s.CATEGORY):
                result.others = {"category": item.get(s.CATEGORY)}

            results.append(result)

            if not item.get(s.MAKEPURE):
                continue

            try:
                makepure.price = get_min_price(item.get(s.MAKEPURE))
                makepure.taxin = True
                if item.get(s.MAKEPURE_BIKO) and "点の新品" in item.get(
                    s.MAKEPURE_BIKO
                ):
                    makepure.condition = "新品"
                else:
                    makepure.condition = "中古"
            except ValueError:
                makepure.price = None
            if not makepure.url:
                makepure.url = item.get(s.MAKEPURE_URL)
            makepure.sub_urls = (
                [item.get(s.MAKEPURE_URL)] if item.get(s.MAKEPURE_URL) else None
            )
            if item.get(s.MAKEPURE_BIKO):
                makepure.stock_msg = item.get(s.MAKEPURE_BIKO)
            results.append(makepure)

    else:
        raise HTTPException(
            status_code=400, detail="URL must contain either '/product/' or 'search?'"
        )

    return items.SearchResults(results=results)

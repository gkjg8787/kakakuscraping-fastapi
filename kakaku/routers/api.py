from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session


from accessor.read_sqlalchemy import get_session
from domain.models.items import items
from accessor import api

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

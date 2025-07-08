from fastapi import APIRouter, Request, Form, Depends, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session


from accessor.read_sqlalchemy import get_session
from domain.models.items import items
from accessor import api

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/items/", response_model=items.ItemCreateResponse)
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


@router.patch("/price/", response_model=items.PriceUpdateResponse)
def api_update_price(
    parseinfos: items.ParseInfosUpdate, db: Session = Depends(get_session)
):
    repo = api.PriceUpdateRepository(db=db)
    response = repo.save(parseinfos=parseinfos)
    return response

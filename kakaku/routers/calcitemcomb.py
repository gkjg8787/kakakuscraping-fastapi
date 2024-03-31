from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from accessor.read_sqlalchemy import get_session
from common import read_templates
from parameter_parser.item import NewestFilterQuery
from parameter_parser.calcitemcomb import (
    ShippingConditionQuery,
    ItemCombinationResultForm,
    SearchShippingQuery,
)
from template_value.calcitemcomb import (
    ItemSelectionContext,
    ShippingConditionContext,
    ItemCombCalcResultContext,
    SearchShippingContext,
)

router = APIRouter(prefix="/calcitemcomb", tags=["calcitemcomb"])
templates = read_templates.templates


@router.get("/select/", response_class=HTMLResponse)
def read_select_item_price_combination(
    request: Request,
    nfq: NewestFilterQuery = Depends(),
    db: Session = Depends(get_session),
):
    isc = ItemSelectionContext(nfq=nfq, db=db)
    return templates.TemplateResponse(
        request=request, name="itemcomb/item_selection.html", context=isc.get_context()
    )


@router.get("/shipping/", response_class=HTMLResponse)
def read_input_shop_shipping_condition(
    request: Request,
    scq: ShippingConditionQuery = Depends(),
    db: Session = Depends(get_session),
):
    scc = ShippingConditionContext(db=db, scq=scq)
    return templates.TemplateResponse(
        request=request,
        name="itemcomb/shipping_condition.html",
        context=scc.get_context(),
    )


@router.post("/result/", response_class=HTMLResponse)
async def read_item_price_combination_result(
    request: Request,
    icr: ItemCombinationResultForm = Depends(),
    db: Session = Depends(get_session),
):
    stores: list[str] = []
    async with request.form() as fm:
        for k, v in fm._dict.items():
            if "item_id" in k:
                continue
            for s in fm.getlist(k):
                store = f"{k}={s}"
                stores.append(store)
    icr.set_store_list(stores)
    iccrc = ItemCombCalcResultContext(icrf=icr, db=db)
    return templates.TemplateResponse(
        request=request,
        name="itemcomb/result_combination.html",
        context=iccrc.get_context(),
    )


@router.get("/shipping/search/", response_class=HTMLResponse)
def read_input_search_shop_shipping(
    request: Request,
    ssq: SearchShippingQuery = Depends(),
    db: Session = Depends(get_session),
):
    ssc = SearchShippingContext(ssq=ssq, db=db)
    return templates.TemplateResponse(
        request=request, name="itemcomb/search_shipping.html", context=ssc.get_context()
    )

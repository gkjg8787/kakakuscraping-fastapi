from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse

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

router = APIRouter(
    prefix="/calcitemcomb"
    ,tags=["calcitemcomb"]
)
templates = read_templates.templates

@router.get("/select/", response_class=HTMLResponse)
def read_select_item_price_combination(request :Request,
                                       nfq: NewestFilterQuery = Depends(),
                                       db :Session = Depends(get_session)
                                       ):
    isc = ItemSelectionContext(request=request, nfq=nfq, db=db)
    context = dict(isc)
    return templates.TemplateResponse(
        "itemcomb/item_selection.html"
        ,context
        )

@router.get("/shipping/", response_class=HTMLResponse)
def read_input_shop_shipping_condition(request :Request,
                                       scq :ShippingConditionQuery = Depends(),
                                       db :Session = Depends(get_session)
                                       ):
    scc = ShippingConditionContext(request=request, scq=scq, db=db)
    context = dict(scc)
    return templates.TemplateResponse(
        "itemcomb/shipping_condition.html"
        ,context
        )


@router.post("/result/", response_class=HTMLResponse)
async def read_item_price_combination_result(request :Request,
                                             icr :ItemCombinationResultForm = Depends(),
                                             db :Session = Depends(get_session)
                                             ):
    stores :list[str] = []
    async with request.form() as fm:
        for k, v in fm._dict.items():
            if 'item_id' in k:
                continue
            for s in fm.getlist(k):
                store = f"{k}={s}"
                stores.append(store)
    icr.set_store_list(stores)
    iccrc = ItemCombCalcResultContext(request=request, icrf=icr, db=db)
    context = dict(iccrc)
    return templates.TemplateResponse(
        "itemcomb/result_combination.html"
        ,context
        )

@router.get("/shipping/search/", response_class=HTMLResponse)
def read_input_search_shop_shipping(request :Request,
                                    ssq :SearchShippingQuery = Depends(),
                                    db :Session = Depends(get_session)
                                    ):
    ssc = SearchShippingContext(request=request, ssq=ssq, db=db)
    context = dict(ssc)
    return templates.TemplateResponse(
        "itemcomb/search_shipping.html"
        ,context
        )
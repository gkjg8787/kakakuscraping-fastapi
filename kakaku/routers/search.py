from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse, HTMLResponse

router = APIRouter(
    prefix="/search"
    ,tags=["search"]
)
from common import (
    read_templates,
)
import template_value.search
from parameter_parser.search import (
    SearchFilterQuery,
    SearchToAddForm,
)

templates = read_templates.templates

@router.get("/", response_class=HTMLResponse)
def read_search(request :Request, sfq :SearchFilterQuery = Depends()):
    searchsite = template_value.search.SearchExternalSiteContext(request=request, sfq=sfq)
    context = dict(searchsite)
    res = templates.TemplateResponse(
        "search/item_search.html"
        ,context
        )
    #if nfq.is_cookie_update():
    #    res.set_cookie(key=cookie_name.NewestCookie.cfilter_str.name, value=nfq.get_cookie())
    return res

@router.post("/add/", response_class=HTMLResponse)
def read_search_add(request :Request, saform :SearchToAddForm = Depends()):
    stac = template_value.search.SearchToAddContext(request=request, saform=saform)
    context = dict(stac)
    res = templates.TemplateResponse(
        "search/add_search.html"
        ,context
        )
    return res
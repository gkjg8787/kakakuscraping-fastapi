from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from accessor.read_sqlalchemy import get_session
from common import (
    read_templates,
)
import template_value.search
from parameter_parser.search import (
    SearchFilterQuery,
    SearchToAddForm,
)

router = APIRouter(prefix="/search", tags=["search"])
templates = read_templates.templates


@router.get("/", response_class=HTMLResponse)
def read_search(request: Request, sfq: SearchFilterQuery = Depends()):
    searchsite = template_value.search.SearchExternalSiteContext(
        request=request, sfq=sfq
    )
    context = dict(searchsite)
    res = templates.TemplateResponse("search/item_search.html", context)
    return res


@router.post("/add/", response_class=HTMLResponse)
def read_search_add(
    request: Request,
    saform: SearchToAddForm = Depends(),
    db: Session = Depends(get_session),
):
    stac = template_value.search.SearchToAddContext(
        request=request, saform=saform, db=db
    )
    context = dict(stac)
    res = templates.TemplateResponse("search/add_search.html", context)
    return res

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
    searchsite = template_value.search.SearchExternalSiteContext(sfq=sfq)
    res = templates.TemplateResponse(
        request=request,
        name="search/item_search.html",
        context=searchsite.get_context(),
    )
    return res


@router.post("/add/", response_class=HTMLResponse)
def read_search_add(
    request: Request,
    saform: SearchToAddForm = Depends(),
    db: Session = Depends(get_session),
):
    stac = template_value.search.SearchToAddContext(saform=saform, db=db)
    res = templates.TemplateResponse(
        request=request, name="search/add_search.html", context=stac.get_context()
    )
    return res

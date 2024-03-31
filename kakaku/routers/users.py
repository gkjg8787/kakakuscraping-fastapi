from urllib.parse import urlencode
from fastapi import APIRouter, Request, Form, Depends, status, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from accessor.read_sqlalchemy import get_session
from common import (
    read_templates,
    cookie_name,
    filter_name,
    const_value,
)
import parameter_parser.item as ppi
import template_value.item

router = APIRouter(prefix="/users", tags=["users"])
templates = read_templates.templates


@router.get("/", response_class=HTMLResponse)
def read_users(
    request: Request,
    nfq: ppi.NewestFilterQuery = Depends(),
    db: Session = Depends(get_session),
):
    if nfq.is_cookie_available():
        return RedirectResponse(
            url=str(request.url_for("read_users"))
            + "?"
            + urlencode(nfq.get_filter_dict()),
            status_code=status.HTTP_302_FOUND,
        )

    nil = template_value.item.NewestItemList(nfq=nfq, db=db)
    res = templates.TemplateResponse(
        request=request, name="users/iteminfo_listview.html", context=nil.get_context()
    )
    if nfq.is_cookie_update():
        res.set_cookie(
            key=cookie_name.NewestCookie.cfilter_str.name, value=nfq.get_cookie()
        )
    return res


@router.get("/fc/")
def read_users_filter_clear(request: Request):
    res = RedirectResponse(
        url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
    )
    res.set_cookie(key=cookie_name.NewestCookie.cfilter_str.name, value="")
    return res


@router.get("/items/add/", response_class=HTMLResponse)
def read_users_items_add(request: Request):
    context = {
        "POST_ITEM_NAME": filter_name.TemplatePostName.ITEM_NAME.value,
        "POST_URL_PATH": filter_name.TemplatePostName.URL_PATH.value,
    }
    return templates.TemplateResponse(
        request=request, name="users/add_item.html", context=context
    )


@router.post("/items/add/result/", response_class=HTMLResponse)
def read_users_items_add_post(
    request: Request,
    addurl: ppi.AddItemUrlForm = Depends(),
    db: Session = Depends(get_session),
):
    aiupc = template_value.item.AddItemUrlPostContext(adduform=addurl, db=db)
    return templates.TemplateResponse(
        request=request, name="users/add_item.html", context=aiupc.get_context()
    )


@router.post("/items/updates/")
def read_users_items_update_all(
    request: Request, item_all_update: str = Form(), db: Session = Depends(get_session)
):
    if (
        not item_all_update
        or item_all_update != filter_name.ItemUpdateValue.ITEM_ALL_UPDATE
    ):
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    uaiupc = template_value.item.UpdateAllItemUrlPostContext(db=db)
    return templates.TemplateResponse(
        request=request, name="users/update_item.html", context=uaiupc.get_context()
    )


@router.get("/items/analysis/", response_class=HTMLResponse)
def read_users_analysis(
    request: Request,
    anaq: ppi.AnalysisBaseQuery = Depends(),
    db: Session = Depends(get_session),
):
    iac = template_value.item.ItemAnalysisContext(anaq=anaq, db=db)
    context = iac.get_context()
    if len(iac.errmsg) > 0:
        return templates.TemplateResponse(
            request=request, name="users/item_analysis_error.html", context=context
        )
    else:
        return templates.TemplateResponse(
            request=request, name="users/item_analysis.html", context=context
        )


@router.get("/items/purchase/", response_class=HTMLResponse)
def read_users_items_purchase(
    request: Request,
    pfq: ppi.ItemPurchaseFilterQuery = Depends(),
    db: Session = Depends(get_session),
):
    ulc = template_value.item.ItemPurchaseContext(db=db, pfq=pfq)
    return templates.TemplateResponse(
        request=request, name="users/item_purchase_list.html", context=ulc.get_context()
    )


@router.post("/items/v/update/", response_class=HTMLResponse)
def read_users_url_update(
    request: Request,
    upurlform: ppi.UpdateItemUrlForm = Depends(),
    db: Session = Depends(get_session),
):
    upiupc = template_value.item.UpdateItemUrlPostContext(upurlform=upurlform, db=db)
    return templates.TemplateResponse(
        request=request, name="users/update_item.html", context=upiupc.get_context()
    )


@router.post("/items/v/update/all/", response_class=HTMLResponse)
def read_users_items_update(
    request: Request,
    upurlallform: ppi.UpdateItemAllUrlForm = Depends(),
    db: Session = Depends(get_session),
):
    upiuallpc = template_value.item.UpdateItemAllUrlPostContext(
        upurlform=upurlallform, db=db
    )
    return templates.TemplateResponse(
        request=request, name="users/update_item.html", context=upiuallpc.get_context()
    )


@router.get("/items/v/", response_class=HTMLResponse)
def read_users_items_view(
    request: Request,
    idq: ppi.ItemDetailQuery = Depends(),
    db: Session = Depends(get_session),
):
    idc = template_value.item.ItemDetailContext(idq=idq, db=db)
    if not idc.has_data():
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    return templates.TemplateResponse(
        request=request, name="users/itemview.html", context=idc.get_context()
    )


@router.post("/items/v/addurl/", response_class=HTMLResponse)
def read_users_items_add_url(request: Request, addurl: ppi.AddUrlForm = Depends()):
    if addurl.item_id == const_value.NONE_ID:
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    aupc = template_value.item.AddUrlInitContext(adduform=addurl)
    return templates.TemplateResponse(
        request=request, name="users/add_url.html", context=aupc.get_context()
    )


@router.post("/items/v/addurl/result/", response_class=HTMLResponse)
def read_users_items_add_url_result(
    request: Request,
    addurl: ppi.AddUrlForm = Depends(),
    db: Session = Depends(get_session),
):
    if addurl.item_id == const_value.NONE_ID:
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    aupc = template_value.item.AddUrlPostContext(adduform=addurl, db=db)
    return templates.TemplateResponse(
        request=request, name="users/add_url.html", context=aupc.get_context()
    )


@router.post("/items/v/name/update/", response_class=HTMLResponse)
def read_users_items_update_item_name(
    request: Request,
    upname: ppi.UpdateItemNameForm = Depends(),
    db: Session = Depends(get_session),
):
    if upname.item_id == const_value.NONE_ID:
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    uinic = template_value.item.UpdateItemNameInitContext(upnameform=upname, db=db)
    return templates.TemplateResponse(
        request=request, name="users/update_itemname.html", context=uinic.get_context()
    )


@router.post("/items/v/name/update/result/", response_class=HTMLResponse)
def read_users_items_update_item_name_result(
    request: Request,
    upname: ppi.UpdateItemNameForm = Depends(),
    db: Session = Depends(get_session),
):
    if upname.item_id == const_value.NONE_ID:
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    uinpc = template_value.item.UpdateItemNamePostContext(upnameform=upname, db=db)
    return templates.TemplateResponse(
        request=request, name="users/update_itemname.html", context=uinpc.get_context()
    )


@router.post("/items/v/url/inact/all/", response_class=HTMLResponse)
def read_users_items_inact_url_all(
    request: Request,
    inactform: ppi.InActAllUrlForm = Depends(),
    db: Session = Depends(get_session),
):
    if inactform.item_id == const_value.NONE_ID:
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    iaaupc = template_value.item.InActAllUrlPostContext(inactform=inactform, db=db)
    return templates.TemplateResponse(
        request=request, name="users/update_act_url.html", context=iaaupc.get_context()
    )


@router.post("/items/v/url/inact/", response_class=HTMLResponse)
def read_users_items_inact_url(
    request: Request,
    inactform: ppi.InActUrlForm = Depends(),
    db: Session = Depends(get_session),
):
    if inactform.item_id == const_value.NONE_ID:
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    iaupc = template_value.item.InActUrlPostContext(inactform=inactform, db=db)
    return templates.TemplateResponse(
        request=request, name="users/update_act_url.html", context=iaupc.get_context()
    )


@router.post("/items/v/url/act/", response_class=HTMLResponse)
def read_users_items_act_url(
    request: Request,
    actform: ppi.ActUrlForm = Depends(),
    db: Session = Depends(get_session),
):
    if actform.item_id == const_value.NONE_ID:
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    iaupc = template_value.item.ActUrlPostContext(actform=actform, db=db)
    return templates.TemplateResponse(
        request=request, name="users/update_act_url.html", context=iaupc.get_context()
    )


@router.post("/items/v/url/remove/", response_class=HTMLResponse)
def read_users_items_url_remove(
    request: Request,
    remurlform: ppi.RemoveItemUrlForm = Depends(),
    db: Session = Depends(get_session),
):
    if remurlform.item_id == const_value.NONE_ID:
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    riupc = template_value.item.RemoveItemUrlPostContext(remurlform=remurlform, db=db)
    return templates.TemplateResponse(
        request=request, name="users/remove_items_url.html", context=riupc.get_context()
    )


@router.get("/items/v/chart/", response_class=HTMLResponse)
def read_users_items_view_chart(
    request: Request,
    idq: ppi.ItemDetailQuery = Depends(),
    db: Session = Depends(get_session),
):
    idcc = template_value.item.ItemDetailChartContext(idq=idq, db=db)
    if not idcc.has_data():
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    return templates.TemplateResponse(
        request=request, name="users/itemview_chart.html", context=idcc.get_context()
    )


@router.post("/items/v/remove/", response_class=HTMLResponse)
def read_users_items_remove(
    request: Request,
    diform: ppi.DeleteItemForm = Depends(),
    db: Session = Depends(get_session),
):
    if not diform.is_valid():
        raise HTTPException(status_code=404, detail="Item not found")
    diic = template_value.item.DeleteItemInitContext(diform=diform, db=db)
    return templates.TemplateResponse(
        request=request, name="users/del_item.html", context=diic.get_context()
    )


@router.post("/items/v/remove/result/", response_class=HTMLResponse)
def read_users_items_remove_result(
    request: Request,
    diform: ppi.DeleteItemForm = Depends(),
    db: Session = Depends(get_session),
):
    if not diform.is_valid():
        raise HTTPException(status_code=404, detail="Item not found")
    dic = template_value.item.DeleteItemContext(diform=diform, db=db)
    return templates.TemplateResponse(
        request=request, name="users/del_item.html", context=dic.get_context()
    )


@router.get("/groups/add/", response_class=HTMLResponse)
def read_users_groups_add(request: Request):
    context = {
        "POST_GROUP_NAME": filter_name.TemplatePostName.GROUP_NAME.value,
    }
    return templates.TemplateResponse(
        request=request, name="users/add_group.html", context=context
    )


@router.post("/groups/add/result/", response_class=HTMLResponse)
def read_users_groups_add_result(
    request: Request,
    addgform: ppi.AddGroupForm = Depends(),
    db: Session = Depends(get_session),
):
    agpc = template_value.item.AddGroupPostContext(addgform=addgform, db=db)
    return templates.TemplateResponse(
        request=request, name="users/add_group.html", context=agpc.get_context()
    )


@router.get("/groups/edit/", response_class=HTMLResponse)
def read_users_groups_edit(
    request: Request,
    groupfilter: ppi.NewestFilterQueryForGroup = Depends(),
    db: Session = Depends(get_session),
):
    editgroup = template_value.item.EditGroupContext(nfqg=groupfilter, db=db)
    if not editgroup.gfid or editgroup.gfid == const_value.NONE_ID:
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    return templates.TemplateResponse(
        request=request, name="users/edit_group.html", context=editgroup.get_context()
    )


@router.post("/groups/edit/update/", response_class=HTMLResponse)
async def read_users_groups_edit_update(
    request: Request,
    giform: ppi.GroupItemUpdateForm = Depends(),
    db: Session = Depends(get_session),
):
    form_dict: dict[str, list] = {}
    async with request.form() as fm:
        for key in [k for k in fm.keys()]:
            form_dict[key] = fm.getlist(key)

    if form_dict:
        giform.set_group_item_list(form_dict)

    ugi = template_value.item.UpdateGroupItem(giform=giform, db=db)

    return RedirectResponse(
        url=str(request.url_for("read_users_groups_edit")) + ugi.get_query(),
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/groups/delete/", response_class=HTMLResponse)
def read_users_groups_delete(
    request: Request,
    delgform: ppi.DeleteGroupForm = Depends(),
    db: Session = Depends(get_session),
):
    if not delgform.is_valid():
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    dgic = template_value.item.DeleteGroupInitContext(delgform=delgform, db=db)
    return templates.TemplateResponse(
        request=request, name="users/del_group.html", context=dgic.get_context()
    )


@router.post("/groups/delete/result/", response_class=HTMLResponse)
def read_users_groups_delete_result(
    request: Request,
    delgform: ppi.DeleteGroupForm = Depends(),
    db: Session = Depends(get_session),
):
    if not delgform.is_valid():
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    dgc = template_value.item.DeleteGroupContext(delgform=delgform, db=db)
    res = templates.TemplateResponse(
        request=request, name="users/del_group.html", context=dgc.get_context()
    )
    res.set_cookie(key=cookie_name.NewestCookie.cfilter_str.name, value="")
    return res


@router.post("/groups/rename/", response_class=HTMLResponse)
def read_users_groups_rename(
    request: Request,
    renamegform: ppi.RenameGroupNameInitForm = Depends(),
    db: Session = Depends(get_session),
):
    if not renamegform.is_valid():
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    dgic = template_value.item.RenameGroupNameInitContext(rgnform=renamegform, db=db)
    return templates.TemplateResponse(
        request=request, name="users/rename_group.html", context=dgic.get_context()
    )


@router.post("/groups/rename/result/", response_class=HTMLResponse)
def read_users_groups_rename_result(
    request: Request,
    renamegform: ppi.RenameGroupNameForm = Depends(),
    db: Session = Depends(get_session),
):
    if not renamegform.is_valid():
        return RedirectResponse(
            url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
        )
    dgic = template_value.item.RenameGroupNameContext(rgnform=renamegform, db=db)
    return templates.TemplateResponse(
        request=request, name="users/rename_group.html", context=dgic.get_context()
    )


@router.get("/urls/v/", response_class=HTMLResponse)
def read_users_urls_view(
    request: Request,
    ufq: ppi.UrlListFilterQuery = Depends(),
    db: Session = Depends(get_session),
):
    ulc = template_value.item.UrlListContext(db=db, ufq=ufq)
    return templates.TemplateResponse(
        request=request, name="users/url_list.html", context=ulc.get_context()
    )


@router.get("/ex/", response_class=HTMLResponse)
def read_users_extract(
    request: Request,
    esfq: ppi.ExtractStoreFilterQuery = Depends(),
    db: Session = Depends(get_session),
):
    nil = template_value.item.ExtractStoreItemListContext(esfq=esfq, db=db)
    res = templates.TemplateResponse(
        request=request,
        name="users/iteminfo_listview_extract.html",
        context=nil.get_context(),
    )
    return res


@router.get("/stores/", response_class=HTMLResponse)
def read_users_stores(
    request: Request,
    slfq: ppi.StoreListFilterQuery = Depends(),
    db: Session = Depends(get_session),
):
    slc = template_value.item.StoreListContext(db=db, slfp=slfq)
    return templates.TemplateResponse(
        request=request, name="users/store_list.html", context=slc.get_context()
    )


@router.get("/stores/postage/edit/", response_class=HTMLResponse)
def read_users_stores_postage_edit(
    request: Request,
    slfq: ppi.StoreListFilterQuery = Depends(),
    db: Session = Depends(get_session),
):
    escc = template_value.item.EditShippingConditionContext(db=db, slfq=slfq)
    return templates.TemplateResponse(
        request=request,
        name="users/edit_shipping_condition.html",
        context=escc.get_context(),
    )


@router.post("/stores/postage/edit/result/", response_class=HTMLResponse)
async def read_users_stores_postage_edit_result(
    request: Request,
    escf: ppi.EditShippingConditionForm = Depends(),
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
    escf.set_store_list(stores)
    escr = template_value.item.EditShippingConditionResult(db=db, escf=escf)
    return templates.TemplateResponse(
        request=request,
        name="users/edit_shipping_condition_result.html",
        context=escr.get_context(),
    )


@router.post("/stores/delete/", response_class=HTMLResponse)
def read_users_store_delete(
    request: Request,
    dsf: ppi.DeleteStoreForm = Depends(),
    db: Session = Depends(get_session),
):
    dsic = template_value.item.DeleteStoreInitContext(db=db, dsf=dsf)
    return templates.TemplateResponse(
        request=request,
        name="users/del_shipping_condition.html",
        context=dsic.get_context(),
    )


@router.post("/stores/delete/result/", response_class=HTMLResponse)
def read_users_store_delete_result(
    request: Request,
    dsf: ppi.DeleteStoreForm = Depends(),
    db: Session = Depends(get_session),
):
    dsc = template_value.item.DeleteStoreContext(db=db, dsf=dsf)
    return templates.TemplateResponse(
        request=request,
        name="users/del_shipping_condition.html",
        context=dsc.get_context(),
    )


@router.get("/onlinestores/", response_class=HTMLResponse)
def read_users_online_stores(
    request: Request,
    slfq: ppi.OnlineStoreListFilterQuery = Depends(),
    db: Session = Depends(get_session),
):
    oslc = template_value.item.OnlineStoreListContext(db=db, slfp=slfq)
    return templates.TemplateResponse(
        request=request, name="users/online_store_list.html", context=oslc.get_context()
    )


@router.get("/onlinestores/cp/", response_class=HTMLResponse)
def read_users_online_stores_copy(
    request: Request,
    oscq: ppi.OnlineStoreCopyToMyQuery = Depends(),
    db: Session = Depends(get_session),
):
    oscc = template_value.item.OnlineStoreCopyContext(db=db, oscq=oscq)
    return templates.TemplateResponse(
        request=request,
        name="users/copy_online_store_list_result.html",
        context=oscc.get_context(),
    )


@router.get("/onlinestores/update/", response_class=HTMLResponse)
def read_users_online_stores_update(
    request: Request, db: Session = Depends(get_session)
):
    osuc = template_value.item.OnlineStoreUpdateContext(db=db)
    return templates.TemplateResponse(
        request=request,
        name="users/update_online_store.html",
        context=osuc.get_context(),
    )

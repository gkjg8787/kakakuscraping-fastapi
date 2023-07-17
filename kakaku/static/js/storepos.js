window.onload = function(){
    addEventRangeButton(document);
    addEventDeleteTermsButton(document);
    addEventAddTermsButton();
}

function addEventDeleteTermsButton(elem) {
    let terms = elem.querySelectorAll('.delete_terms_button');
    for (let t of terms){
        t.addEventListener('click', () => {
            if (t.parentNode.parentNode.className != 'shippingterms') { return; }
            t.parentNode.parentNode.remove();
        });
    }
}

function addEventAddTermsButton(){
    let addbtn = document.querySelectorAll('.shippingterms_add_button');
    for(let a of addbtn){
        a.addEventListener('click',() => {
            addShippingTerms(a);
        });
    }
}


function addEventRangeButton(elem) {
    let crbs = elem.querySelectorAll('.change_range_button, .change_single_button');

    for (let crb of crbs) {
        let bopedic = getBOpeDict(crb.previousElementSibling);
        crb.addEventListener('click', () => {
            if (crb.value == '→') {
                crb.value = '←';
                crb.title = '条件を単一にする';
                createRangeBOpe(crb, bopedic);
            } else {
                crb.value = '→';
                crb.title = '条件を範囲にする';
                deleteRangeBOpe(crb);
            }
            crb.classList.toggle('change_range_button');
            crb.classList.toggle('change_single_button');
        });
    }
}

function addShippingTerms(elem){
    let idxdict = {terms_idx:1}
    if ( elem.parentNode.previousElementSibling != null){
        idxdict = getBOpeDict(elem.parentNode.previousElementSibling.querySelector('.b_operator1'));
        idxdict['terms_idx'] = Number(idxdict['terms_idx']) + 1;
    } else {
        idxdict['store_idx'] = getStoreIdx(elem.parentNode.parentNode);
    }
    let st = createShippingTerms(idxdict);
    elem.parentNode.before(st);
    addEventDeleteTermsButton(st);
    addEventRangeButton(st);
}
function toElementFromHTML(htmltext){
    let elem = document.createElement('div');
    elem.innerHTML = htmltext;
    return elem.firstElementChild;
}
function createShippingTerms(idxdict){
    let terms_number = idxdict['terms_idx'];
    let terms_index = idxdict['terms_idx'];
    let store_index = idxdict['store_idx'];
    let boundary_1 = '';
    let postage = '';
    let created_at = getDate();
    let innerhtml = `
    <div class="shippingterms">
    <span class="shippingterms_boundary">
        <span class="terms_name">条件${terms_number}</span>
        <span class="input_title boundary_input_title">合計</span>
        <input type="number" name="stores[${store_index}][terms][${terms_index}][boundary][]" class="boundary1" value="${boundary_1}">
        <span class="boundary_unit">円</span>
        <select name="stores[${store_index}][terms][${terms_index}][b_ope][]" class="b_operator1" title="範囲不等号">
            <option hidden>未選択</option>
            <option value="gt" >より大きい</option>
            <option value="ge" >以上</option>
            <option value="lt" >未満</option>
            <option value="le" >以下</option>
        </select>
        <input type="button" value="→" class="change_range_button" title="条件>を範囲にする">
    </span>
    <span class="if_connect_text">なら</span>
    <span class="shippingterms_postage">
        <span class="input_title">送料</span>
        <input type="number" name="stores[${store_index}][terms][${terms_index}][postage]" value="${postage}"/>
        <span class="postage_unit">円</span>
        <span class="shippingterms_created_at">
            <span class="created_at">${created_at}</span>
        </span>
    </span>
    <span class="shippingterms_button">
        <input type="button" class="delete_terms_button" value="削除">
    </span>
    </div>
    `;
    return toElementFromHTML(innerhtml);
}
function getDate(){
    let d = new Date();
    let month = getZeroFillFormat(d.getMonth()+1, 2);
    let date = getZeroFillFormat(d.getDate(), 2);
    let hours = getZeroFillFormat(d.getHours(), 2);
    let minutes = getZeroFillFormat(d.getMinutes(), 2);
    let seconds = getZeroFillFormat(d.getSeconds(), 2);
    let df = `${d.getFullYear()}-${month}-${date} ${hours}:${minutes}:${seconds}`;
    return df;
}
function getZeroFillFormat(val, digit){
    return ('0'+val).slice(-digit);
}

function getStoreIdx(storeterms_box_elem){
    sname_elem = storeterms_box_elem.previousElementSibling;
    if (sname_elem.className != 'input_storename'){ return; }
    let ary = sname_elem.name.split(/\[|\]/);
    return ary[1];
}

function getBOpeDict(bope_elem) {
    let dic = new Array();
    let ary = bope_elem.name.split(/\[|\]/);
    dic['store_idx'] = ary[1];
    dic['terms_idx'] = ary[5];
    return dic;
}

function deleteRangeBOpe(crb_elem) {
    crb_elem.parentNode.querySelector('.range_and').remove();
    crb_elem.parentNode.querySelector('.boundary2').remove();
    crb_elem.parentNode.querySelector('.b_operator2').remove();
}

function createRangeBOpe(crb_elem, idxdict) {
    let store_index = idxdict['store_idx'];
    let terms_index = idxdict['terms_idx'];
    let boundary_2 = '';
    let range_terms = `
    <span class="range_and">かつ</span>
    <input type="number" name="stores[${store_index}][terms][${terms_index}][boundary][]" class="boundary2" value="${boundary_2}">
    <select name="stores[${store_index}][terms][${terms_index}][b_ope][]" class="b_operator2" title="範囲不等号">
        <option hidden>未選択</option>
        <option value="gt" >より大きい</option>
        <option value="ge" >以上</option>
        <option value="lt" >未満</option>
        <option value="le" >以下</option>
    </select>
    `;
    crb_elem.insertAdjacentHTML('beforebegin', range_terms)
}


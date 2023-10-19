window.onload = function(){
    addSearchBtnEvent();
}
function addSearchBtnEvent(){
    document.querySelector('#search-button').addEventListener("click", searchItemInSelect);
    document.querySelector('#search-word').addEventListener('keydown',(e)=>{
        if (e.keyCode === 13){
            searchItemInSelect();
        }
    });
}
function searchItemInSelect(){
    let resultDiv = document.querySelector('#search-result');

    let searchWord = document.querySelector('#search-word').value;
    const post_name = document.querySelector('#item-select').name;
    let options = document.querySelectorAll("select option");
    let results = [];
    for (const option of options) {
        if (option.textContent.toLowerCase().includes(searchWord.toLowerCase())) {
            results.push(option);
        }
    }
    resultDiv.innerHTML = "";
    for (const result of results) {
        resultDiv.appendChild(createSearchResult(result, post_name));
    }
}
function toElementFromHTML(htmltext){
    let elem = document.createElement('div');
    elem.innerHTML = htmltext;
    return elem.firstElementChild;
}
function createSearchResult(elem, post_name){
    let text = elem.text;
    let val = elem.value;
    let innerhtml = `
    <div>${text}<button type="submit" class="search-result-select" id="search-selected-${val}" name="${post_name}" value="${val}">選択</button>
    </div>
    `;
    return toElementFromHTML(innerhtml);
}

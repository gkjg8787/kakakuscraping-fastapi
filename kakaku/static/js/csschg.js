window.onload = function(){
    let targets = document.querySelectorAll(`input[type='checkbox'][id='listview_checkbox']`);

    for(let target of targets) {
        target.addEventListener('change', function() {
            base_path = document.getElementById("cssSearchResult").href;
            parent_str = base_path.split('/');
            dirname = parent_str.slice(0, parent_str.length-1).join('/');
            if ( target.checked ){
                document.getElementById("cssSearchResult").href = dirname + "/retlist.css";
                if (!hasListViewParam()){ addListViewParam(); }
            } else {
                document.getElementById("cssSearchResult").href = dirname + "/retsearch.css";
                if (hasListViewParam()){ removeListViewParam(); }
            }
        });
        if(target.checked){
            if (!hasListViewParam()){ addListViewParam(); }
        } else {
            if (hasListViewParam()){ removeListViewParam(); }
        }
    }
    function hasListViewParam(){
        let urls = document.querySelectorAll('.pageurl')
        if (urls.length == 0){ return false; }
        let ptn = '&listview=1';
        for( let url of urls ){
            let newurl = new URL(url['href']);
            if(newurl.searchParams.get('listview')){ return true; }
            return false;
        }
        return false;
    }
    function addListViewParam(){
        addURLParam('.pageurl', 'listview', 1);
        addURLParam('.prepage', 'listview', 1);
        addURLParam('.folpage', 'listview', 1);
    }
    function addURLParam(selector, param, val){
        let urls = document.querySelectorAll(selector);
        for(let url of urls){
            let newurl = new URL(url['href']);
            if(!newurl.searchParams.get(param)){
                newurl.searchParams.append(param, val);
                url['href'] = newurl.href;
            }
        }
    }
    function removeListViewParam(){
        removeURLParam('.pageurl', 'listview');
        removeURLParam('.prepage', 'listview');
        removeURLParam('.folpage', 'listview');
    }
    function removeURLParam(selector, param){
        let urls = document.querySelectorAll(selector);
        for(let url of urls){
            let newurl = new URL(url['href']);
            if(newurl.searchParams.get(param)){
                newurl.searchParams.delete(param);
                url['href'] = newurl.href;
            }
        }
    }
};

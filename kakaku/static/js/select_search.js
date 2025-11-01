/**
 * select要素のオプションを検索する機能を提供する。
 * 
 * 使い方:
 * 1. このファイルをHTMLから読み込む。
 * 2. 検索機能を適用したいselect要素を含むコンテナに `searchable-select-container` クラスを追加する。
 * 3. コンテナ内に以下の要素を配置する。
 *    - 検索対象のselect要素: `searchable-select` クラス
 *    - 検索UIの表示/非表示を切り替えるボタン: `toggle-search-btn` クラス
 *    - 検索UI全体を囲むコンテナ: `search-ui-container` クラス
 *    - 検索キーワード入力ボックス: `search-box` クラス
 *    - 検索結果表示エリア: `search-results` クラス
 */
document.addEventListener('DOMContentLoaded', function() {
    const containers = document.querySelectorAll('.searchable-select-container');

    containers.forEach(container => {
        const toggleBtn = container.querySelector('.toggle-search-btn');
        const searchUiContainer = container.querySelector('.search-ui-container');
        const searchBox = container.querySelector('.search-box');
        const searchResults = container.querySelector('.search-results');
        const storeSelect = container.querySelector('.searchable-select');

        if (!toggleBtn || !searchUiContainer || !searchBox || !searchResults || !storeSelect) {
            console.error('Required elements for searchable select not found in a container.', container);
            return;
        }

        const options = Array.from(storeSelect.options);

        toggleBtn.addEventListener('click', function(event) {
            event.stopPropagation(); // documentのクリックイベントが発火しないようにする
            const isHidden = searchUiContainer.style.display === 'none';
            searchUiContainer.style.display = isHidden ? 'block' : 'none';
            if (isHidden) {
                searchBox.focus();
            }
        });

        searchBox.addEventListener('input', function() {
            const keyword = this.value.trim().toLowerCase();
            searchResults.innerHTML = '';

            if (keyword.length === 0) return;

            const filteredOptions = options.filter(option => 
                option.text.toLowerCase().includes(keyword) && option.value !== ""
            );

            filteredOptions.forEach(option => {
                const resultItem = document.createElement('div');
                resultItem.textContent = option.text;
                resultItem.className = 'search-result-item'; // スタイル付けのためのクラス
                resultItem.addEventListener('click', function() {
                    storeSelect.value = option.value;
                    storeSelect.dispatchEvent(new Event('change', { bubbles: true }));
                    searchUiContainer.style.display = 'none';
                    searchBox.value = '';
                });
                searchResults.appendChild(resultItem);
            });
        });
    });

    // ドキュメントのどこかをクリックしたときに検索UIを閉じる
    document.addEventListener('click', function(event) {
        containers.forEach(container => {
            const searchUiContainer = container.querySelector('.search-ui-container');
            if (searchUiContainer.style.display === 'block' && !container.contains(event.target)) {
                searchUiContainer.style.display = 'none';
            }
        });
    });
});
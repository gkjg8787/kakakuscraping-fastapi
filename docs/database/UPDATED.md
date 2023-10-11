## データベースのUPDATEについて

### 登録済みURLの変更について
+ サイトの更新等でURLパスを変更する必要がある場合、TOOLを使用することでURLを手動で変更することができます。<br>※DBをTOOLで更新する前にバックアップを取っておいてください。
  0. 前提：コンテナを作成済み
  1. dockerコンテナのIDを調べる。
   + `docker ps -a`
  2. 変更したいURLのドメイン、変更箇所の文字列、変更後の文字列を指定してツールを起動します。
    + `docker exec -it [コンテナID] python3 tool/db_url_update.py [domain] [src string] [converted string]`

### 対応するサイトの更新について
+ 2023/10/11 駿河屋の一部のURLの変更
  + URL階層：(product-other)から(product/other)へ変更
+ 2023/9/19 ブックオフのURLの変更
  + ドメイン：(www.bookoffonline.co.jp)から(shopping.bookoff.co.jp)へ変更
  + URL階層：(old)から(used)へ変更
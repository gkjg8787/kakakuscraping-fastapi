# kakakuscraping-fastapi

## 概要
+ 特定のサイトページをスクレイピングして価格情報をデータベースに保存します。<br>
    対象サイト
     + 駿河屋
     + ブックオフオンライン
     + ネットオフ
     + ゲオオンラインストア
+ アイテムやグループとしてまとめて一覧で管理することができます。
+ 複数のアイテムを送料込みの価格でどこの店で購入すると安いかを計算しサポートします。

### dockerで動かす
0. 前提：dockerをインストール済み
1. ダウンロードしたディレクトリ内のDockerfileがある場所で以下のコマンドを実行しイメージを作成します。<br>
   `docker build -t kakaku-build:test .`
2. 次のコマンドでイメージを実行<br>
   `docker run --init -p 8000:8000 --name kakaku -it kakaku-build:test`
3. 実行できたらURLにアクセスしてください。<br>
   `http://127.0.0.1:8000`

### 使い方
+ #### URLを追加<br>
  + 検索して追加<br>
    操作メニューの**アイテムを探して追加**から外部サイトを検索して追加することができます。
  + 直接URLを指定して追加<br>
    操作メニューの**アイテム追加**からURLを指定して追加することができます。※対象サイトの商品ページのみ
+ #### URLを更新<br>
  操作メニューの**一括情報取得**もしくはアイテム毎の情報取得から登録したURLの情報を取得します。
  URLの更新にはバックサーバを起動する必要があります。
  + バックサーバ<br>
    操作メニューの**管理画面**から移動して、起動する必要があります。稼働中でURLの更新ができます。
+ #### 価格計算<br>
  登録したアイテムを選択し、送料条件を入力することで送料込みの最安値の組み合わせを出力することができます。<br>
  ***※常に最安値がでるとは限らないので参考程度にして下さい***<br>
  操作メニューの**アイテムの価格計算**からできます。
+ #### 注意<br>
  + URLの追加をしたら更新しないと反映されません。
  + 対象サイトがエラーを返した場合は取得に失敗します。
  + 対象サイトのHTML構造が変わると取得できません。
  + 1つのアイテムに沢山のURLを登録すると価格計算が終わらないかもしれません。

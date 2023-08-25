## PostgreSQLへの変更
+ ### 設定ファイルの入れ替え
  + [kakakuscraping](kakakuscraping)にあるDockerfile、及びrequirements.txtをソースのあるディレクトリの同名ファイルへ上書きしてください。
  ### settings.pyの変更
  + kakaku/settings.pyのDATABASESにPostgreSQLの設定を追加または変更してください。
  + 参照されるのは"default":... , "old_db":... ,となっている設定です。
    + PostgreSQL以外の設定が"default":..., "old_db":... となっている場合は別の文字列に変更してください。
    + PostgreSQLの設定が"default", "old_db"以外の場合（例："postgre_default":..., "postgre_old_db":...)、"default", "old_db"へ変更してください。
  ### Dockerの再作成
  + ファイルの入れ替え、設定の変更を行ったらDockerを再作成してください。
+ ### docker-composeの例
  + postgreSQLをdokcer-composeで使用する例がこのディレクトリに配置されています。
  + #### dockerコンテナ作成方法
    + ソースフォルダ(kakaku)を[kakakuscraping配下](kakakuscraping)へ配置してください。
    + 配置したkakaku配下に対して、上記のsettings.pyの変更をしてください。
    + `docker compose up`で起動します。
    + docker起動後、PostgreSQLのコンテナが起動するまでお待ちください。
    + PostgreSQL起動後、fastapiのコンテナでテーブル作成のコマンドを実行する必要があります。
      + `docker ps -a`で起動したfastapiのコンテナのCONTAINER IDを確認します。
      + 以下のコマンドでテーブルを作成します。CONTAINER IDの部分は上記で確認したIDを入れます。<br>
      `docker exec -it [CONTAINER ID] python3 db_util.py create`
    + 実行できたらURLにアクセスしてください。<br>
    `http://127.0.0.1/kakaku/`
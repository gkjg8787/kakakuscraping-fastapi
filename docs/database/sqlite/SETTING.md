## SQLiteへの変更
+ ### 設定ファイルの入れ替え
  + このディレクトリにあるDockerfile、及びrequirements.txtをソースのあるディレクトリの同名ファイルへ上書きしてください。
  ### settings.pyの変更
  + kakaku/settings.pyのDATABASESにsqliteの設定を追加または変更してください。
  + 参照されるのは"default":... , "old_db":... ,となっている設定です。
    + sqliteの設定以外が"default", "old_db"になっている場合は文字列を変更してください。
    + sqliteの設定が"default", "old_db"以外の場合は各設定を"default", "old_db"に変更してくだい。
  ### Dockerの再作成
  + ファイルの入れ替え、設定の変更を行ったらDockerを再作成してください。
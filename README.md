# Lightning Node Database

このプロジェクトは、SQLite3を使用してLightning Networkノードチャネルのための時系列データを管理するように設計されています。チャネルリストとチャネルデータの取得、データベースの更新、および指定された保持期間に基づいて古いデータを削除するオプション機能を提供します。

## プロジェクト構造

python 3.11.3
poetry 1.5.1

```
lightning-node-db
├── src
│   ├── __init__.py
│   ├── main.py
│   ├── db
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── models.py(no use)
│   ├── api
│   │   ├── __init__.py
│   │   ├── lightning_client.py
│   │   └── node_service.py(no use)
│   ├── utils
│   │   ├── __init__.py
│   │   └── config.py
│   └── cli
│       ├── __init__.py
│       └── lnddb.py
├── data
│   └── .gitkeep
├── tests
│   ├── __init__.py
│   ├── test_database.py
│   └── test_node_service.py
├── config.yaml
└── README.md
```

## 機能

1. **チャネルリスト管理**: Lightning Networkノードからチャネルのリストを取得し更新します。
2. **チャネルデータ保存**: 各チャネルの残高や手数料を含む時系列データを保存します。
3. **データ保持**: 指定された保持期間に基づいて古いデータを削除するオプション。
4. **SQLite3データベース**: 軽量で効率的なデータ保存のためにSQLite3を使用します。

## インストール

1. リポジトリをクローンします:
   ```
   git clone <repository-url>
   cd lightning-node-db
   ```

2. 必要なパッケージをインストールします:
   ```
   poetry install
   ```

3. config.yamlを編集してデータベース接続の詳細と保持期間を設定し、アプリケーションを構成します。

### config.yamlの設定パラメータ

```yaml
database:
  path: "data/lightning_nodes.db"  # データベースファイルのパス
  retention_period_months: 3    # "--delete"オプションで３か月分保存して他は削除

lightning:
  api_url: "https://127.0.0.1:8080"  # Lightning node API アドレス
  macaroon_path:  "C:/XXXX/XXXX" # macaroonファイルのパス
  tls_path: "C:/XXXX/XXXX" # ファイルのパス

amboss:
  api_key: "your amboss api key" # ambossにアクセスするための API KEY
  api_url: "https://api.amboss.space"
```

## 使用方法

アプリケーションを実行するには、次のコマンドを実行します:
```
poetry run python src/main.py
```

また、コマンドラインオプションを使用して古いデータを管理することもできます:
```
python src/main.py --delete <number_of_months>
```
「定期的に実行することで、データの増大を防ぎます。」　
　　

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルをご覧ください。

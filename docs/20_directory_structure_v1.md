# ディレクトリ構成（v1）

## 基本構成

```
Q-APP-V2/
├── frontend/         # Next.js
├── backend/          # FastAPI
├── docker-compose.yml
├── .devcontainer/
│   ├── frontend/
│   │   └── devcontainer.json
│   └── backend/
│       └── devcontainer.json
├── docs/
├── issues/
└── .github/
```

## 意味

- **2つの独立したdevcontainer**: frontendとbackendで別々の開発環境
- **docker-compose.yml**: 共通サービス（PostgreSQL等）を定義
- **VS Code**: frontend用とbackend用の2つのウィンドウで開発

## メリット

- コンテナ側AIがfrontend/backend独立して作業可能
- 各環境に必要なツール/拡張機能を分離
- 並行開発が容易
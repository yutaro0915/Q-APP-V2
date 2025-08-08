# ローカル開発環境セットアップ

## 必要な環境

- PostgreSQL 16
- Python 3.11 (uv管理)
- Node.js 20

## 初回セットアップ

### 1. PostgreSQL セットアップ
```bash
brew install postgresql@16
brew services start postgresql@16
createdb campus_sns  
psql campus_sns -f docs/03a_ddl_postgresql_v1.sql
```

### 2. Backend セットアップ
```bash
cd backend
uv sync --all-extras  # 依存関係とdev依存関係をインストール
```

### 3. Frontend セットアップ  
```bash
cd frontend
npm install
```

## 開発開始

### 自動起動スクリプト
```bash
./scripts/dev-start.sh
```

### 手動起動
```bash
# Terminal 1: Backend
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend  
cd frontend && npm run dev
```

## テスト実行
```bash
./scripts/test.sh
```

## カスタムコマンド

### ホスト側（Issue管理）
- `/issue-create` - YAMLからIssue作成
- `/pr-review` - PRレビュー＆マージ  
- `/progress-update` - 進捗CSV更新

### Backend開発
- `/backend-work` - Issue実装
- `/backend-verify` - テスト実行
- `/backend-fix` - エラー修正

### Frontend開発
- `/frontend-work` - Issue実装
- `/frontend-verify` - テスト実行  
- `/frontend-fix` - エラー修正

## 環境変数
- backend/.env - DATABASE_URL等
- frontend/.env.local - NEXT_PUBLIC_API_BASE等
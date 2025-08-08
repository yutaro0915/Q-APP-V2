# 九大学内SNS Q-APP-V2

## 開発環境セットアップ

### 前提条件
- Docker Desktop または Rancher Desktop
- VS Code + Dev Containers拡張機能
- claude CLI（ホスト側）

### 起動方法

1. VS Codeで開発環境を起動

**Backend開発**:
- VS Codeで「Open Folder in Container」を選択
- `.devcontainer/backend`を選択

**Frontend開発**:
- 新しいVS Codeウィンドウで「Open Folder in Container」を選択
- `.devcontainer/frontend`を選択

2. サービスの起動

Backend:
```bash
uvicorn app.main:app --reload --host 0.0.0.0
```

Frontend:
```bash
npm run dev
```

### テスト実行

Backend:
```bash
pytest
```

Frontend:
```bash
npm test
```
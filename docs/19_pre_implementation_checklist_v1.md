# 実装開始前チェックリスト（v1）

## 必須準備

### 1. ディレクトリ構造
```
Q-APP-V2/
├── api/
│   ├── app/
│   ├── tests/
│   └── requirements.txt
├── front/
│   ├── app/
│   ├── components/
│   ├── __tests__/
│   └── package.json
├── docs/
├── issues/
└── .github/
    └── workflows/
```

### 2. 開発環境
- [ ] devcontainer設定（.devcontainer/）
- [ ] docker-compose.yml（postgres含む）
- [ ] 環境変数テンプレート（.env.example）

### 3. 初期ファイル
- [ ] .gitignore
- [ ] DDL適用スクリプト（03a_ddl_postgresql_v1.sql）
- [ ] package.json / requirements.txt（最小限の依存）

### 4. CI/CD
- [ ] GitHub Actions基本設定
- [ ] ブランチ保護ルール（mainへの直接push禁止）
- [ ] PR時の自動テスト実行

### 5. 開発規約
- [ ] linter設定（ESLint/Prettier/ruff）
- [ ] テストフレームワーク（pytest/vitest）
- [ ] コミットメッセージ形式

### 6. Issue準備
- [ ] Phase 0のYAML作成
- [ ] 依存関係の確認
- [ ] 最初の3-5個のIssue選定

## 追加検討事項

### 抜けている可能性
- **ローカル開発手順書**: 最初にcloneした人が環境構築できるか
- **認証トークンの扱い**: 開発時のモックトークン
- **CORS設定**: ローカル開発時の設定
- **PR/Issueテンプレート**: .github/に配置
- **初回起動確認**: Hello Worldレベルの動作確認

### 最小限のスタート
Phase 0を最小構成で始めて、必要に応じて追加する方針でも可。
重要なのは「最初のPRがマージできる状態」を作ること。
# CI戦略（v1）

## 基本方針

すべてのPRで自動テストを実行し、ドキュメントとの整合性を保つ。

## CIチェック項目

### 1. テスト実行
- **Backend**: pytest（DDL適用済みのPostgreSQLに対して）
- **Frontend**: vitest
- **必須**: すべてのPRでGREEN

### 2. 変更ファイル数制限
- 本体ファイル + テストファイルの**2ファイル以下**
- docs/、issues/、.github/ は除外

### 3. ドキュメント整合性

#### DDL整合性
- テスト実行前に `03a_ddl_postgresql_v1.sql` を適用
- これによりスキーマとコードの不一致を検出

#### API仕様整合性
- `api-change` ラベルがある場合、OpenAPI仕様を検証
- 実装とYAML定義の乖離を防ぐ

## 実行タイミング

```yaml
on:
  pull_request:
    branches: [main]
```

## 失敗時の対処

### テスト失敗
- エラーログを確認
- DDLとの不整合の可能性を確認

### ファイル数超過
- 対象外ファイルの混入を確認
- 必要なら Issue を分割

### 仕様不整合
- ドキュメント更新が必要か確認
- 実装が仕様から逸脱していないか確認

## 今後の拡張

- linter/formatter追加（Phase 0完了後）
- E2Eテスト（Phase 1完了後）
- パフォーマンステスト（Phase 2以降）
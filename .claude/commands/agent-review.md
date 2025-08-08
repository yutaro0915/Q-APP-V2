# レビューコマンド（main直コミット後の検証運用）

[アプリ概要 / 参照ガイド]
- 重要ドキュメント
  - `docs/04_api_contract_v1.yaml`（OpenAPI 契約）
  - `docs/04a_api_schemas_dto_v1.md`（DTO/Validation/カーソル例）
  - `docs/04b_api_conventions_v1.md`（X-Request-Id/エラー/RateLimit/カーソル）
  - `docs/03_data_model_erd_v1.md` / `docs/03a_ddl_postgresql_v1.sql`（DDL/インデックス/派生値）
  - `docs/05_backend_design_fastapi_v1.md`（レイヤ/シグネチャ/Tx/Hot/検索）
  - `docs/06_frontend_design_nextjs_v1.md`（データ受け渡し/CSR/SSR）
- 不変条件（抜粋）: 認証（不透明トークン/7日）、ID（prefix_ULID）、コメントASC、リアクション409、SolveのNOT_APPLICABLE、20件固定/200上限、ErrorResponse統一。

目的: PRなしで main へ直接反映されるため、コミット後に即時の自動テストと仕様照合を行い、必要であれば直ちにフォローアップコミット/リバートを実施する。

前提: 重要仕様は `docs/04* / 03* / 05 / 06` に準拠。テストは `scripts/test.sh` を使用。

## 1) 直近コミットの抽出
```bash
# 直近の対象コミットを1件（または範囲）特定
LAST_COMMIT=$(git rev-parse HEAD)
PREV_COMMIT=$(git rev-parse HEAD^)
```

## 2) 変更点の検証（One-File Rule / YAMLスタンプ）
```bash
# 実装ファイルの変更数（docs/issues/.github とテスト除外）
git diff --name-only "$PREV_COMMIT" "$LAST_COMMIT" | \
  grep -v '^docs/' | grep -v '^issues/' | grep -v '^\.github/' | \
  grep -v '^backend/tests/' | grep -v '^frontend/__tests__/' | \
  wc -l

# YAMLが変更されていれば先頭スタンプを確認
for f in $(git diff --name-only "$PREV_COMMIT" "$LAST_COMMIT" | grep '^issues/.*\.yaml$' || true); do
  head -n 10 "$f" | grep -q '^# claim:' && echo "claim OK in $f" || echo "no claim in $f (許容: 実装のみのコミットなど)"
done
```

## 3) 自動テスト
```bash
bash scripts/test.sh || { echo "Tests failed. 要フォローアップ"; exit 1; }
```

## 4) 仕様/DoDの突合（目視またはスクリプト）
- 変更された実装ファイルと対応する `issues/**.yaml` を開き、`spec_refs / specification / constraints / test_specification / DoD` に整合するか確認。
- 逸脱があれば、最小のフォローアップコミットで修正。

## 5) CSV更新
```bash
# 必要に応じ、対象ID行を更新（status/notes/end_at など）
# 例: notesへ "post-commit review: ok" を追記するなど
# （簡易運用のため、手編集→コミット）
vi docs/issues_progress_index.csv

git add docs/issues_progress_index.csv
git commit -m "chore(progress): post-commit review updated"
git push origin main
```

## 6) リバートが必要な場合
```bash
git revert --no-edit "$LAST_COMMIT" && git push origin main
# 直後に修正版のコミットを作成（TDD→GREEN→コミット）
```

## チェックリスト（レビュー観点）
- YAMLの DoD を満たしている
- ErrorResponse/X-Request-Id/認証規約が遵守されている
- カーソル/スナップショットの扱いが正しい
- DDL準拠の列名/制約を破っていない
- 既存のテストを壊していない（GREEN）
- 追加の影響範囲が最小（One-File Rule実質順守）

# 実装コマンド（main直コミット・YAMLスタンプ運用）

[アプリ概要 / 参照ガイド]
- プロダクト: Kyudai Campus SNS v1（API/Next.js フロント）
- 重要ドキュメント（必読・索引）
  - `docs/04_api_contract_v1.yaml`: OpenAPI 3.0.3 本契約（paths/components）
  - `docs/04a_api_schemas_dto_v1.md`: DTO/Validation 仕様（ID形式・カーソルJSON例・各DTO）
  - `docs/04b_api_conventions_v1.md`: 共通規約（認証・X-Request-Id・エラー・カーソル・RateLimit）
  - `docs/03_data_model_erd_v1.md`: ERD/派生値/インデックス/代表クエリ
  - `docs/03a_ddl_postgresql_v1.sql`: DDL（PostgreSQL 16）
  - `docs/05_backend_design_fastapi_v1.md`: レイヤと責務・代表シグネチャ・Tx/副作用・Hot/検索・Cursor
  - `docs/06_frontend_design_nextjs_v1.md`: ルーティング・CSR/SSR方針・Props
  - 参考: `docs/07_*`（S3）、`docs/08_*`（SLO/Sec）、`docs/09_*`（Deploy）
- コア不変条件（要点）
  - 認証: /auth/bootstrap→不透明トークン、DBは sessions.token_hash 照合、TTL≈7日。
  - ID: `^(usr|cre|ses|thr|cmt|att|rcn)_[0-9A-HJKMNP-TV-Z]{26}$`（ULID）。
  - スレ/コメント: 画像は各1枚（P3実装）、コメントはASC/ネスト無し/ソフト削除。
  - リアクション: スレ up/save、コメント up、重複は409。
  - 解決: 質問スレのみ、非適用は400 VALIDATION_ERROR（details.reason=NOT_APPLICABLE）。
  - ページング: 20固定、cursor=base64url(JSON)、上限200。Hot/検索は snapshotAt 固定（24h）。
  - エラー: 04bのErrorResponse、全応答に X-Request-Id。
- 代表クエリのキー（タプル比較）
  - TL new: (createdAt DESC, id DESC)
  - TL hot: (score DESC, createdAt DESC, id DESC)
  - コメント: (createdAt ASC, id ASC)

目的: ブランチ/PRを使わず、main上で最小コミットを積み上げて進捗を管理する。各タスクは YAML スタンプで占有し、TDDでGREEN確認後にコミットする。1コミットあたりの実装ファイルは原則1つ（テストは除外）。

前提: 重要仕様は `docs/04* / 03* / 05 / 06` に準拠。テストは `scripts/test.sh` で backend/frontend をまとめて実行。

## 0) プレフライト（任意・簡易）
```bash
git pull --rebase  # mainを最新化（簡易）
```

## 1) YAML選定と占有スタンプ（即コミット・最小）
```bash
ISSUE_YAML="issues/phase2/P2-API-Repo-Comments-Insert.yaml"  # 着手するYAML
AGENT="your_agent_name"                                     # 任意の識別子

# 既に占有されていないか確認（先頭10行）
head -n 10 "$ISSUE_YAML" | grep -q '^# claim:' && { echo "Already claimed: $ISSUE_YAML"; exit 1; }

# 占有スタンプをYAML先頭に付与
ISSUE_ID=$(basename "$ISSUE_YAML" .yaml)
STAMP=$(cat <<EOF
# claim:
#   id: $ISSUE_ID
#   assignee: ${AGENT}
#   start_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
#   note: ""
EOF
)
# 先頭に差し込む（macOS対応）
printf "%s\n" "$STAMP" | cat - "$ISSUE_YAML" > "$ISSUE_YAML.tmp" && mv "$ISSUE_YAML.tmp" "$ISSUE_YAML"

# すぐにコミット（占有を可視化）
git add "$ISSUE_YAML" && git commit -m "chore(issue-claim): $ISSUE_ID start (assignee=$AGENT)" && git push
```

## 2) TDD（RED→GREEN、コミットはGREEN後のみ）
```bash
# 実装対象とテストファイルのパスをセット
IMPL_FILE="backend/app/repositories/comments_repo.py"   # 例: 実装ファイル
TEST_FILE="backend/tests/test_comments_insert.py"      # 例: テストファイル

# まずテストを書いて RED を確認（コミットはしない）
# ... テスト編集 ...
bash scripts/test.sh || echo "RED（まだコミットしない）"

# 実装して GREEN にする（必要に応じてリファクタ）
# ... 実装編集 ...
bash scripts/test.sh  # GREENになるまで繰り返す
```

## 3) コミット（実装1 + テストのみ）
```bash
# 最終テスト（GREENでなければコミットしない）
bash scripts/test.sh || { echo "Tests failed. Commit aborted."; exit 1; }

# 実装1 + テストのみをコミット（One-File Ruleは自律判断）
git add "$IMPL_FILE" "$TEST_FILE" && git commit -m "feat($ISSUE_ID): implement & test" && git push
```

## 4) YAMLによる完了報告（CSVは任意・簡易）
```bash
# YAMLの末尾に完了コメントブロックを追記して可視化（CSVは任意）
COMPLETE=$(cat <<EOF
# done:
#   finished_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
#   result: GREEN
#   note: ""
EOF
)
printf "\n%s\n" "$COMPLETE" >> "$ISSUE_YAML"
git add "$ISSUE_YAML" && git commit -m "chore(issue-done): $ISSUE_ID finished" && git push
```

## 問題発生時（YAMLへ追記して完了にしない）
```bash
# YAMLに障害メモを残す（doneは付けない）
ISSUE_NOTE=$(cat <<EOF
# issue:
#   at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
#   note: "症状/原因/対処メモ"
EOF
)
printf "\n%s\n" "$ISSUE_NOTE" >> "$ISSUE_YAML"
git add "$ISSUE_YAML" && git commit -m "chore(issue-note): $ISSUE_ID incident noted" && git push
```

## 重要な原則
- YAMLスタンプは「開始の即時可視化」のため最初に単独コミット
- 実装コミットは「実装1ファイル＋テスト」へ厳格に限定
- 各コミット前に `bash scripts/test.sh` を必ず実行（GREEN以外はコミット禁止）
- 仕様差異が発生したら、まずYAMLを更新し整合させてから実装

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

## 0) プレフライト（mainを最新に）
```bash
# ルートで実行
git fetch origin && git checkout main && git pull --rebase origin main
```

## 1) YAML選定と占有スタンプ（即コミット）
```bash
# 変数を設定
ISSUE_YAML="issues/phase2/P2-API-Repo-Comments-Insert.yaml"  # 着手するYAMLに置換
AGENT="your_agent_name"

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

# すぐに main へコミット/プッシュ（占有を可視化）
git add "$ISSUE_YAML"
git commit -m "chore(issue-claim): $ISSUE_ID を占有開始 (assignee=$AGENT)"
git pull --rebase origin main && git push origin main
```

## 2) TDD（ローカルでRED→GREEN、コミットはGREEN後のみ）
```bash
# 実装対象とテストファイルのパスをセット
IMPL_FILE="backend/app/repositories/comments_repo.py"   # 例: 実装ファイル
TEST_FILE="backend/tests/test_comments_insert.py"      # 例: テストファイル

# まずテストを書いて RED を確認（コミットはしない）
# ... テスト編集 ...
bash scripts/test.sh || echo "RED OK（まだコミットしない）"

# 実装して GREEN にする（必要に応じてリファクタ）
# ... 実装編集 ...
bash scripts/test.sh  # ここは必ずGREENになるまで繰り返す
```

## 3) コミット（実装1 + テストのみ）
```bash
# 非メタ・非テストの変更ファイル数を事前チェック（原則1つ）
CHANGED_IMPL_COUNT=$(git diff --name-only | \
  grep -v '^docs/' | grep -v '^issues/' | grep -v '^\.github/' | \
  grep -v '^backend/tests/' | grep -v '^frontend/__tests__/' | \
  wc -l | tr -d ' ')
if [ "$CHANGED_IMPL_COUNT" -gt 1 ]; then
  echo "Error: 変更中の実装ファイルが複数あります（1つに分割してください）"; exit 1;
fi

# 念のため再テスト（GREENであること）
bash scripts/test.sh || { echo "Tests failed. Commit aborted."; exit 1; }

# 変更対象のみを明示的にステージしてコミット（実装1 + テスト）
git add "$IMPL_FILE" "$TEST_FILE"
COMMIT_MSG="feat($ISSUE_ID): 実装/テストを追加（One-File Rule厳守）"
git commit -m "$COMMIT_MSG"

# main へ反映
git pull --rebase origin main && git push origin main
```

## 4) CSV更新（任意・main運用）
```bash
# 最低限、開始・完了時刻とステータスを追記/更新（手作業でも可）
# 新規行の追加例（必要な列だけ一時的に埋める）。空欄は後で補完可。
echo "$ISSUE_ID,phase?,layer?,area?,action?,$IMPL_FILE,$TEST_FILE,main,$AGENT,COMPLETED,,labels?,$(date -u +%Y-%m-%dT%H:%M:%SZ),$(date -u +%Y-%m-%dT%H:%M:%SZ)," >> docs/issues_progress_index.csv

git add docs/issues_progress_index.csv
git commit -m "chore(progress): $ISSUE_ID の進捗をCSVに反映"
git pull --rebase origin main && git push origin main
```

## 失敗時のリカバリ
```bash
# ワーキングツリーを破棄してやり直し
git restore -SW .

# 直前のコミットを元に戻す（mainに誤って入れた場合）
# 影響が大きければ revert を使い、その後に修正版を再コミット
git revert --no-edit HEAD && git push origin main
```

## 重要な原則
- YAMLスタンプは「開始の即時可視化」のため最初に単独コミット
- 実装コミットは「実装1ファイル＋テスト」へ厳格に限定
- 各コミット前に `bash scripts/test.sh` を必ず実行（GREEN以外はコミット禁止）
- 仕様差異が発生したら、まずYAMLを更新し整合させてから実装

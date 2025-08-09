# テスト運用コマンド（統合テスト/契約検証/フォローアップIssue発行）

[アプリ概要 / 参照ガイド]
- 重要ドキュメント（契約と整合を厳密確認）
  - `docs/04_api_contract_v1.yaml`（OpenAPI 契約）
  - `docs/04a_api_schemas_dto_v1.md`（DTO/Validation/カーソル例）
  - `docs/04b_api_conventions_v1.md`（X-Request-Id/エラー/RateLimit/カーソル）
  - `docs/03_data_model_erd_v1.md` / `docs/03a_ddl_postgresql_v1.sql`（DDL/インデックス/派生値）
  - `docs/05_backend_design_fastapi_v1.md`（レイヤ/シグネチャ/Tx/Hot/検索）
  - `docs/06_frontend_design_nextjs_v1.md`（データ受け渡し/CSR/SSR）
- 不変条件（抜粋）
  - 認証（不透明トークン/7日、`sessions.token_hash` 照合、JWT不使用）
  - ID（prefix_ULID）、20件固定/最大200（カーソル=base64url(JSON)）
  - ErrorResponse統一（全応答に `X-Request-Id`）、RateLimitヘッダ（429時）
  - 並び：new=(createdAt DESC, id DESC)、comments=(createdAt ASC, id ASC)

[目的]
- 実装は行わず、テストの円滑化・総合テスト・契約検証・回帰防止の仕組み化を担当。
- 現在作業中のフェーズ（phaseX）の「コミット済みタスク」に対し、統合テストを実行し、逸脱があれば最小単位の修正Issue（YAML）を発行する。

[基本原則]
- フェーズ順守: 対象は現在作業中の `issues/phaseX/` のみ。
- One-File Rule尊重: 本エージェントは実装を変更しない。必要なのは追加テスト or 修正Issue（YAML）の発行。
- 仕様優先: 04/04a/04b/03/03a/05/06 に従い、テストは契約を正にする。

[環境準備]
```bash
# Backend（uv 仮想環境はCI同一系）
cd backend && uv sync --extra dev && cd -

# Frontend
cd frontend && npm ci --no-audit --no-fund --prefer-offline && cd -
```

## 1) 対象フェーズの決定とタスク抽出
```bash
# 現在の対象フェーズ（手動指定推奨。未指定時はphase1を既定）
PHASE_NUM=${PHASE_NUM:-1}
PHASE_DIR="issues/phase${PHASE_NUM}"

# 作業対象のYAML（コミット済みタスクのうち、先頭に # claim: があるもの）
mapfile -t CLAIMED < <(grep -l '^# claim:' ${PHASE_DIR}/*.yaml || true)
echo "[info] phase${PHASE_NUM} claimed issues: ${#CLAIMED[@]}"

# 参考: 完了済みも別途集計
mapfile -t DONE < <(grep -l '^# done:' ${PHASE_DIR}/*.yaml || true)
echo "[info] phase${PHASE_NUM} done issues: ${#DONE[@]}"
```

## 2) ベースライン実行（既存テスト）
```bash
# まずは既存テストをGREEN確認（watch無効）
cd frontend && npm test -- --run || { echo "[fail] frontend"; exit 1; }; cd -
bash scripts/test.sh || { echo "[fail] suite"; exit 1; }
```

## 3) 契約/統合テスト（Router→Service→Repo）
目的: モックが隠す齟齬（返却形/ヘッダ/順序/カーソル）を検出。
```bash
# 対象: 作業中フェーズのうち、Threads系とAuth系の代表ケース
# 例: 一覧(new)/詳細/作成/削除/セッション/APIヘッダ

INTEG_DIR="backend/tests/integration"
mkdir -p "$INTEG_DIR"

# サンプル（一覧 new の返却形・順序・nextCursor・ヘッダ）
cat > "$INTEG_DIR/test_threads_integration_list_new.py" <<'PY'
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_list_new_contract_and_order():
    client = TestClient(app)
    r = client.get("/api/v1/threads?sort=new")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "items" in data and isinstance(data["items"], list)
    # nextCursor は None/str のいずれか
    assert ("nextCursor" not in data) or (data["nextCursor"] is None or isinstance(data["nextCursor"], str))
    # ヘッダ: X-Request-Id
    assert "X-Request-Id" in r.headers
PY

# 実行
cd backend && uv run pytest -q tests/integration/test_threads_integration_list_new.py && cd -
```

検査観点（増やす場合のテンプレ）:
- 返却DTOスキーマ: `ThreadDetail`/`PaginatedThreadCards` の必須/nullable/型
- エラー形式/ヘッダ: `ErrorResponse`、429系ヘッダ（RateLimit）
- 並び順の安定性: (createdAt DESC, id DESC) での境界（同一createdAt）
- カーソルのencode/decodeと`v=1` 等の検証

## 4) スナップショット/回帰ガード
```bash
SNAP_DIR="backend/tests/snapshots"
mkdir -p "$SNAP_DIR"
cat > "$SNAP_DIR/test_threads_snapshot_contract.py" <<'PY'
from fastapi.testclient import TestClient
from app.main import app

EXPECTED_KEYS = {"items", "nextCursor"}

def test_threads_list_new_shape_snapshot():
    client = TestClient(app)
    r = client.get("/api/v1/threads?sort=new")
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()).issubset(EXPECTED_KEYS)
PY

cd backend && uv run pytest -q tests/snapshots/test_threads_snapshot_contract.py && cd -
```

## 5) OpenAPI/DTO突合（オプション）
```bash
# 例: pydanticモデル→jsonschema生成し、04のOpenAPI components/schemas と簡易突合（差分検出のみ）
# 実装は省略（必要時にテストファイルを追加）。
```

## 6) 逸脱が見つかった場合のIssue発行（修正タスクのYAMLを追加）
原則: 本エージェントは実装を変更しない。最小単位の修正Issue（YAML）を発行し、`# claim:` を付けずにコミット。
```bash
PHASE_NUM=${PHASE_NUM:-1}
PHASE_DIR="issues/phase${PHASE_NUM}"

ISSUE_ID="P${PHASE_NUM}-FIX-<Area>-<Action>-<ShortName>"
ISSUE_PATH="${PHASE_DIR}/${ISSUE_ID}.yaml"

cat > "$ISSUE_PATH" <<'YAML'
id: P1-FIX-EXAMPLE-Contract-Mismatch
phase: 1
layer: API
area: Service
action: Threads-Contract-Mismatch
target_file: backend/app/services/threads_service.py
test_file: backend/tests/test_threads_service.py
depends_on: ["P1-API-Repo-Threads-ListNew", "P1-API-Service-Threads-ListNew"]
spec_refs:
  - "04a"  # DTO
  - "04b"  # 規約
  - "05"   # 責務
estimated_loc: 20

specification:
  purpose: "Service↔Repo 返却形式の不一致（{items,nextCursor}）を是正"
  content_requirements:
    - "list_threads_new 入出力の整合（items→ThreadCard[], nextCursor透過）"
    - "不正cursorは ValidationException(400)"

output_format: "Python 実装（Serviceのみ）＋テスト（One-File Rule）"

constraints:
  - "Router/Repo/DTOは変更しない"

test_specification:
  validation:
    - "モックRepo返却 {items,nextCursor} での変換と透過を確認"

definition_of_done:
  - "全体テストGREEN"
YAML

git add "$ISSUE_PATH" && git commit -m "chore(issues): add fix issue $ISSUE_ID (no-claim)" && git push
```

## 7) レポート
- 実行結果・検出差分・発行したIssue一覧を短報でまとめ、必要に応じて `docs/issues_progress_index.csv` を更新。

## 付録: テスト強化チェックリスト
- 実配線テスト（Router→Service→Repo）
- スナップショット（DTO形状）
- 並び順境界（タプル比較）
- ヘッダ規約（X-Request-Id/429ヘッダ）
- OpenAPI/DTO突合
- フロント`lib/api.ts` と ErrorResponse の型整合（vitest）


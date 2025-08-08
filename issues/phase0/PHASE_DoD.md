# Phase 0 — 環境初期化（セットアップ）DoD（受け入れ条件）

このフェーズの目的は、以降の実装を安全・効率に進めるための最小限の基盤（API/Front/CI/Infra手順/運用ルール）を整えることです。アプリとしての動作はヘルスチェックまでを保証します。

## 達成状態（ゴール）
- リポジトリ構成が確立（`docs/20_directory_structure_v1.md` 準拠）。
  - `backend/` FastAPI 雛形、`frontend/` Next.js 雛形、`docs/`、`issues/`、`scripts/`、`.github/workflows/` が存在。
- API が起動し、`GET /api/v1/health` が 200 OK を返す（JSON: `{"status":"healthy"}`）。
- エラー形式とリクエストID規約が有効化。
  - `X-Request-Id` ミドルウェア導入：全応答にヘッダ付与（要求IDを尊重、無ければ生成）。
  - 統一 `ErrorResponse` へ例外変換（04b のコード・details・requestId 準拠）。
- フロントの雛形画面が表示できる（Next.js App Router 初期ページ・デザイントークン・APIクライアント雛形）。
- CI が PR で自動実行され、green である。
  - backend ユニットテスト（health）が成功。
  - frontend テスト（初期）が成功。
  - One-File Rule 検査、OpenAPI 検証（必要時）、プロンプト/CSV チェックが通過。
- インフラ初期化手順が揃っている（適用/運用は次フェーズ以降）。
  - RDS/S3/AppRunner/VPC Connector それぞれの手順書（docs/09_*）が参照可能。

## 実装・設定必須事項（抜粋）
- Backend
  - `backend/app/main.py`（アプリ初期化、CORS 設定、Request-Id ミドルウェア、例外ハンドラ登録）。
  - `backend/app/util/errors.py`（ErrorResponse/例外→HTTP 変換）。
  - `backend/app/routers/health.py` 実装（/api/v1/health）。
  - ユーティリティ：`util/idgen.py`（prefix_ULID）、`services/cursor.py`（base64url(JSON)）。
- Frontend
  - `app/layout.tsx` / `app/page.tsx` 雛形、`app/globals.css`（デザイントークン反映）。
  - 薄い API クライアント（Bearer 付与は後続）。
- CI
  - `.github/workflows/ci.yml`（backend/frontend テスト、One-File Rule、OpenAPI validate、CSV/プロンプト検査）。

## 受け入れテスト（例）
- `GET /api/v1/health` が 200/JSON/Content-Type: application/json で応答する。
- 任意エンドポイントの失敗時、`ErrorResponse` 形式・`X-Request-Id` 付で返ること（ダミーハンドラでも可）。
- PR を作成すると CI 全ジョブが成功する。

## 参照
- 04b_api_conventions_v1.md（X-Request-Id / ErrorResponse / RateLimit 規約）
- 05_backend_design_fastapi_v1.md（レイヤ構成・横断事項）
- 20_directory_structure_v1.md / 21_ci_strategy_v1.md / 13_workflow_devcontainer_v1.md

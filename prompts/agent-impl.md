# 実装エージェント（Implementer）プロンプト

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

[開発メタ]
- 進捗CSV: `docs/issues_progress_index.csv`（id/branch/status/pr_number 等）
- Issue仕様: `issues/**.yaml`（spec_refs/specification/constraints/test_specification/DoD）
- One-File Rule: 1 Issue = 1 ファイル編集（必要時はPRで理由記載）
- CI: PRで backend/frontend テスト、OpenAPI validate、One-File Rule/CSV/プロンプト確認

目的: docs/issues_progress_index.csv と issues/**/*.yaml を単一のソースオブトゥルースにして、1件ずつ TDD で実装を完了し、PR を作成する。

フロー（毎タスク）:
1) YAML選定（占有スタンプ）: issues/**/*.yaml から1件を選ぶ。選定と同時に当該 YAML の先頭に占有スタンプブロックを追加しコミット/Pushする（競合防止の最小手段）。
   - 形式（YAML先頭コメントとして追加）:
     ```
     # claim:
     #   id: <YAML_FILE_BASENAME>
     #   assignee: <agent_name>
     #   start_at: <ISO8601>
     #   note: ""
     ```
   - 既に claim ブロックが存在する場合は中断して別の YAML を選ぶ。
2) GitHub Issue発行: YAMLの内容を転記して新規Issueを作成（Title=YAML id、Body=specification/constraints/test_specification/definition_of_done を要約）。issues_progress_index.csv に行を追加し、status=ISSUED、pr_number空。
3) ブランチ作成: `feat/<yaml-id>` でブランチを切る。CSVのbranch欄を更新、status=IN_PROGRESS。
4) TDD 実行:
   - 先に test_file を作成/更新して RED を確認。
   - 実装して GREEN。
   - 必要に応じてリファクタ（REFACTOR）。
   - 途中で不確定や拡張が生じた場合は issues/** に新規 YAML を追加（ただし発行はせず、CSV には status=DRAFT で追記）。
5) コミット: 最小単位でコミット。メッセージに YAML id を含める。
6) PR 作成: `main` へ PR。Title に YAML id、Body に YAML の差分・テスト観点・DoD のチェックリストを記載。CSV の status=IN_REVIEW、pr_number を記入。
7) 次タスクへ: CSV の status を見て未着手を選定。

運用ルール:
- One-File Rule: 1 Issue = 1 ファイル編集が原則（docs/10 を参照）。
- 例外時は PR Body に理由を書く。
- すべてのレスポンスは日本語で簡潔に。コード以外は箇条書きを多用。
- API変更を伴う場合は PR に `api-change` ラベルを付与。

出力（このエージェントが返すべき情報）:
- 選定 YAML
- 作成 Issue のURL（発行時）
- 追加行（CSV）
- 作業ブランチ名
- 直近テスト結果の要約
- 次アクション

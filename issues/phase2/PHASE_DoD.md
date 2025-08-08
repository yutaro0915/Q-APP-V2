s# Phase 2 — コメント/リアクション/解決/プロフィール DoD

このフェーズの目的は、スレッドに対するコミュニケーション機能（コメント/Up/保存/解決）とプロフィール表示/編集を、契約/DDLに合致する形で完成させることです。

## 達成状態（ゴール）
- コメント機能一式（作成・一覧・削除）がASC固定、20件固定カーソルで安定動作。
- リアクション（スレ: up/save、コメント: up）が 409 を正しく返し、成功時は常に 204。
- 解決フラグの設定/解除が「質問スレ」のみ許可され、非適用は 400（NOT_APPLICABLE 詳細付き）。
- プロフィールの取得/部分更新が動作（公開フラグ/値の整合、JOIN付与）。
- すべての応答が `X-Request-Id` を付与、エラーは `ErrorResponse` 形式。

## API 完了条件
- コメント
  - `POST /threads/{id}/comments`（Bearer）→ CreatedResponse
  - `GET /threads/{id}/comments?cursor=`（公開）→ PaginatedComments（ASC, (createdAt,id)）
  - `DELETE /comments/{id}`（Bearer, authorのみ）→ 204（削除済みは404扱い）
- リアクション
  - `POST /threads/{id}/reactions` {kind: 'up'|'save'} → 204 / 409
  - `POST /comments/{id}/reactions` {kind: 'up'} → 204 / 409
- 解決
  - `POST /threads/{id}/solve` {commentId: string|null} → 204（質問スレのみ、詳細必須）
- プロフィール
  - `GET /auth/me/profile`（Bearer）→ MyProfile
  - `PATCH /auth/me/profile`（Bearer）→ 204（部分更新、*_publicのみも可）

## DB/Repo 仕様（抜粋）
- `comments`: id, thread_id, author_id, body, up_count, created_at, deleted_at。
- `reactions`: UNIQUE(user_id,target_type,target_id,kind)。`INSERT ... ON CONFLICT DO NOTHING`、影響1行のみカウント増。
- コメント作成時に `threads.last_activity_at = now()`（同Tx）。
- 解決コメント削除時は同Txで `threads.solved_comment_id = NULL`。

## サービス/ルーター
- コメント：DTO検証→Repo→CreatedResponse/ASCページング→削除表示置換（"[削除済み]")。
- リアクション：重複は409、成功は204（べき等）。
- 解決：質問スレ判定→適用/解除、非適用は400（details.reason=NOT_APPLICABLE）。
- プロフィール：公開ON/OFFの動的付与（JOIN users）。

## フロント
- コメントUI（一覧/投稿/削除）、Up/保存ボタン、解決ピン表示。
- プロフィール編集画面（学部≤50、年1..10、公開フラグ）。

## 受け入れテスト（例）
- コメント作成/一覧/削除がGREEN（ASCカーソルの重複無し）。
- リアクション重複時に409、成功時204。
- 解決：質問以外で400（NOT_APPLICABLE詳細付き）。
- プロフィール：公開フラグON/OFFに応じた付与が変わる。

## 参照
- 04/04a/04b/03/03a/05/06（各該当章）
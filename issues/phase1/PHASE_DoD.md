# Phase 1 — コア掲示板（スレ作成/閲覧/削除）DoD

このフェーズの目的は、最小の掲示板体験（スレッド作成・一覧・詳細・削除）を、契約/DDL/設計に厳密に適合させて完成させることです。

## 達成状態（ゴール）
- OpenAPI 04 / DTO 04a / 規約 04b / ERD 03 / DDL 03a / 設計 05 に完全準拠。
- スレッドの作成/一覧（new）/詳細/削除が API で動作し、フロントからも操作可能。
- 認証ブートストラップとセッション確認が最小限動作。
- 一覧カーソル（new）が安定（重複/抜け無し）。
- すべての応答が `X-Request-Id` を付与、エラーは `ErrorResponse` 形式。

## API 完了条件
- `POST /threads`（Bearer 必須）
  - Req: CreateThreadRequest（title 1..60, body 0..2000, tags ≤4, imageKey? null）
  - Res: CreatedResponse（id, createdAt）
- `GET /threads?sort=new`（公開）
  - Res: PaginatedThreadCards（items,nextCursor）
  - 並び: (createdAt DESC, id DESC)、20固定・最大200。
- `GET /threads/{id}`（公開）
  - Res: { thread: ThreadDetail }
- `DELETE /threads/{id}`（Bearer, authorのみ）→ 204
- 認証
  - `POST /auth/bootstrap` → { userId, token, expiresAt }
  - `GET /auth/session`（Bearer）→ { userId } / 401

## DB/Repo 仕様（抜粋）
- `threads`: id, author_id, title, body, up_count, save_count, solved_comment_id, heat, created_at, last_activity_at, deleted_at。
- Repo は純SQL、部分Indexとタプル比較に配慮。
- ソフト削除時の表示置換（返却時にタイトル/本文を "[削除済み]"）。

## サービス/ルーター
- 作成：DTO検証→Tx（threads INSERT, tags ≤4, attachments(任意)）→CreatedResponse。
- 一覧：カーソル（base64url(JSON)）decode→安定 ORDER → nextCursor。
- 詳細：JOIN users し公開属性を付与（AuthorAffiliation）。
- 削除：権限チェック → 204。ErrorResponse/403/404 を整備。

## フロント
- TL（new）: SSR 初期表示、CSRでページング継続。
- ThreadDetail: SSRで詳細（コメントはPhase2以降接続）。
- ThreadForm: 作成フロー確立（Bearer付与）。

## 受け入れテスト（例）
- スレ作成/一覧/削除のユニットテスト（backend）と基本表示（frontend）がGREEN。
- カーソル2ページ目で重複が無い。

## 参照
- 04/04a/04b/03/03a/05/06（各該当章）
# Phase 3 — 画像/検索/タグ DoD

このフェーズの目的は、画像アップロード（S3直PUT）と添付表示、全文検索（pg_trgm）を導入し、ユーザー体験を拡張しつつ契約に一致させることです。

## 達成状態（ゴール）
- 画像: Presign→PUT→作成API imageKey 受理→DTOへURL/有無が付与される一連の動作が成立（各投稿/コメント 0/1枚）。
- 検索: `/search` が relevance/new で動作し、snapshotAt 固定・カーソルで安定ページング（24h）。
- すべての応答が `X-Request-Id` を付与、エラーは `ErrorResponse` 形式。Presign は Bearer 必須。

## API 完了条件
- アップロード
  - `POST /uploads/presign`（Bearer）Req=PresignRequest{mime,size} → Res=PresignResponse{key,url,headers}
  - MIME: image/webp|jpeg|png、size ≤ 5MB、有効期限=300秒
- 添付
  - attachments テーブル連携（XOR: thread_id or comment_id、MIME CHECK）
  - ThreadCard/ThreadDetail/Comment DTO へ hasImage/imageUrl|imageThumbUrl を付与（S3_PUBLIC_BASE + key）
- 検索
  - `GET /search?q&sort=relevance|new&cursor=`（公開）→ PaginatedThreadCards
  - relevance: pg_trgm 類似度 + 軽い時間減衰、new: createdAt DESC
  - X-Snapshot-At ヘッダ付与、24h 超過は 400

## DB/Repo 仕様（抜粋）
- `attachments`: id, key, mime, width, height, size, sha256, created_at, thread_id? xor comment_id?、MIME CHECK。
- `threads.title/body` の GIN(trgm) インデックス、`comments` の部分Index（ASC）既存利用。

## サービス/ルーター
- Presign: mime/size 検証→S3 PUT URL 生成（headers含む）。
- 画像DTO統合: attachments 参照→hasImage + URL 付与（削除時は非表示）。
- 検索: クエリ正規化→repo→PaginatedThreadCards 整形、ヘッダ `X-Snapshot-At`。

## フロント
- 画像前処理（長辺2048, EXIF除去, WebP推奨）→Presign→PUT→imageKey 受け渡し。
- 画像表示コンポーネント（フルスクリーン Viewer）。
- 検索ページ（検索ボックス/結果一覧/ページング/ソート切替）。

## 受け入れテスト（例）
- Presign: 正常発行200、不正MIME/sizeで400。
- 検索: relevance/new ともに2ページ目が重複しない、snapshot期限切れで400。
- DTO: 画像ありスレ/コメントにURL/hasImageが付与。

## 参照
- 04/04a/04b/03/03a/05/06/07（各該当章）
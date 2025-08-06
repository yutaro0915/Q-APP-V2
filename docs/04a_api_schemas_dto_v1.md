04a_api_schemas_dto_v1.md — DTO / Validation（v1・フリーズ）
参照: 01_domain_invariants_v1.md / 03_data_model_erd_v1.md / 03a_ddl_postgresql_v1.sql / 04_api_contract_v1.yaml / 04b_api_conventions_v1.md

0. 共通規約
ID形式：^(usr|cre|ses|thr|cmt|att|rcn)_[0-9A-HJKMNP-TV-Z]{26}$

日時：ISO8601 UTC（例 2025-08-06T09:00:00Z）

文字列前処理：trim()、制御文字/NULLを拒否。改行は保持（excerptのみ空白化）。

ページング：cursor = base64url(JSON)。1ページ20件固定、最大200件。
Hot/検索は初回応答の snapshotAt で並び固定（24h）。

1. Auth
1.1 BootstrapRequest
ts
コピーする
編集する
{ device_secret?: string /* ≤256 */ }
1.2 BootstrapResponse
ts
コピーする
編集する
{ userId: string; token: string; expiresAt: string /* ISO8601 */ }
1.3 SessionResponse
ts
コピーする
編集する
{ userId: string }
2. Profile
2.1 MyProfile
ts
コピーする
編集する
{
  userId: string;              // usr_*
  faculty?: string | null;     // ≤50
  year?: number | null;        // 1..10
  faculty_public: boolean;     // default false
  year_public: boolean;        // default false
}
2.2 UpdateMyProfileRequest
ts
コピーする
編集する
type UpdateMyProfileRequest = Partial<{
  faculty: string | null;      // null で未設定に戻す
  year: number | null;         // null で未設定に戻す
  faculty_public: boolean;
  year_public: boolean;
}>
検証：faculty 1..50、year 1..10。値が無くても *_public は受理（表示は付与されない）。

3. Uploads（S3 Presign）
3.1 PresignRequest
ts
コピーする
編集する
{ mime: 'image/webp'|'image/jpeg'|'image/png', size: number /* 1..5_242_880 */ }
3.2 PresignResponse
ts
コピーする
編集する
{ key: string; url: string; headers: { 'Content-Type': string } }
クライアントは長辺2048pxへ縮小＋EXIF除去後に PUT url。作成APIには imageKey=key を渡す。

imageKey 形式検証：^uploads/\d{4}/\d{2}/[A-Za-z0-9_.-]+\.(webp|jpg|jpeg|png)$

4. Threads / Comments DTO
4.1 Tag
ts
コピーする
編集する
{ key: '種別'|'場所'|'締切'|'授業コード', value: string }
制約：1スレ最大4個、key重複不可。

種別 は スラッグ：question|notice|recruit|chat

場所 1..50、授業コード 1..32、締切 YYYY-MM-DD

4.2 CreateThreadRequest
ts
コピーする
編集する
{
  title: string;             // 1..60
  body?: string;             // 0..2000（省略時は "" に正規化）
  tags?: Tag[];              // ≤4、'種別'はスラッグ、重複キー不可
  imageKey?: string | null;  // presignキー
}
4.3 CreateCommentRequest
ts
コピーする
編集する
{ body: string /* 1..1000 */, imageKey?: string | null }
4.4 著者公開属性
ts
コピーする
編集する
type AuthorAffiliation = { faculty?: string; year?: number };
付与条件：ユーザー側の faculty_public/year_public が true かつ値が非NULLの項目のみ。両方無ければ null を返す。

4.5 表示用 DTO
4.5.1 ThreadCard
ts
コピーする
編集する
{
  id: string; title: string; excerpt: string; tags: Tag[]; heat: number; replies: number; saves: number;
  createdAt: string; lastReplyAt?: string | null;
  hasImage: boolean; imageThumbUrl?: string | null;
  solved: boolean;                              // ★追加：質問スレで解決済みなら true。他種別は常に false
  authorAffiliation?: AuthorAffiliation | null;
}
excerpt：本文から（改行→空白、連続空白圧縮、最大120字、超過時のみ … 付与）。

サムネ：v1はオリジンURLをそのまま返す（TLはCSSで16:9トリミング）。

4.5.2 ThreadDetail
ts
コピーする
編集する
{
  id: string; title: string; body: string; tags: Tag[];
  upCount: number; saveCount: number;
  createdAt: string; lastActivityAt: string;
  solvedCommentId?: string | null;              // 解決コメントのID。解除時は null
  hasImage: boolean; imageUrl?: string | null;
  authorAffiliation?: AuthorAffiliation | null;
}
4.5.3 Comment
ts
コピーする
編集する
{
  id: string; body: string; createdAt: string; upCount: number;
  hasImage: boolean; imageUrl?: string | null;
  authorAffiliation?: AuthorAffiliation | null;
}
4.6 ページングラッパ
ts
コピーする
編集する
type PaginatedThreadCards = { items: ThreadCard[]; nextCursor?: string | null };
type PaginatedComments    = { items: Comment[];    nextCursor?: string | null };
5. Reactions / Solve
5.1 ReactionRequestThread
ts
コピーする
編集する
{ kind: 'up' | 'save' }
5.2 ReactionRequestComment
ts
コピーする
編集する
{ kind: 'up' }
5.3 SolveRequest
ts
コピーする
編集する
{ commentId: string | null } // nullで解除
適用対象：質問（種別=question）スレのみ解決設定を許可。
それ以外の種別への操作は 400 VALIDATION_ERROR（details: [{field:'thread.tags', reason:'NOT_APPLICABLE', required:'question'}]）。

検証：commentId は同一スレ内・未削除。違反は 404。

6. Cursor JSON（例）
すべて base64url でクエリ ?cursor= に載せる。v=1 必須。

TL(new)

json
コピーする
編集する
{ "v":1, "sort":"new", "anchor":{"createdAt":"2025-08-06T08:12:34Z","id":"thr_01J..."} }
TL(hot)

json
コピーする
編集する
{ "v":1, "sort":"hot", "snapshotAt":"2025-08-06T09:00:00Z",
  "anchor":{"score":12.3456,"createdAt":"2025-08-05T23:11:00Z","id":"thr_01J..."} }
コメント(ASC)

json
コピーする
編集する
{ "v":1, "anchor":{"createdAt":"2025-08-06T01:02:03Z","id":"cmt_01J..."} }
検索(relevance)

json
コピーする
編集する
{ "v":1, "sort":"relevance", "q":"配当", "snapshotAt":"2025-08-06T09:00:00Z",
  "anchor":{"score":0.8123,"id":"thr_01J..."} }
期限：snapshotAt が 24h 超過で 400。

上限：1クエリで 最大200件 到達時は nextCursor を返さない。

7. 共通レスポンス
7.1 CreatedResponse
ts
コピーする
編集する
{ id: string; createdAt: string }
7.2 ErrorResponse
ts
コピーする
編集する
{
  error: {
    code: 'VALIDATION_ERROR'|'UNAUTHORIZED'|'FORBIDDEN'|'NOT_FOUND'|'CONFLICT'|'RATE_LIMITED'|'INTERNAL',
    message: string,
    details?: Array<Record<string, any>>,
    requestId?: string
  }
}
details の例（NOT_APPLICABLE）

json
コピーする
編集する
{
  "error":{
    "code":"VALIDATION_ERROR",
    "message":"Invalid operation",
    "details":[{"field":"thread.tags","reason":"NOT_APPLICABLE","required":"question"}]
  }
}
8. E2E例
8.1 TL（Hot, 1ページ目）
json
コピーする
編集する
{
  "items":[
    {
      "id":"thr_01J...",
      "title":"機械学習概論Q3の解釈、これで合ってる？",
      "excerpt":"確率的勾配降下法の…",
      "tags":[{"key":"種別","value":"question"},{"key":"締切","value":"2025-08-10"}],
      "heat":64,"replies":3,"saves":1,
      "createdAt":"2025-08-06T10:12:00Z","lastReplyAt":"2025-08-06T10:20:11Z",
      "hasImage":true,"imageThumbUrl":"https://{bucket}.s3.{region}.amazonaws.com/uploads/2025/08/abc.webp",
      "solved": false,
      "authorAffiliation":{"faculty":"工学部","year":3}
    }
  ],
  "nextCursor":"eyJ2IjoxLCJzb3J0IjoiaG90Iiwic25hcHNob3RBdCI6IjIwMjUtMDgtMDZUMDk6MDA6MDBaIiwiYW5jaG9yIjp7InNjb3JlIjoxMi4zNDUsImNyZWF0ZWRBdCI6IjIwMjUtMDgtMDVUMjM6MTE6MDBaIiwiaWQiOiJ0aHJfMDFKLi4uIn19"
}
8.2 解決設定 → 204
json
コピーする
編集する
// POST /threads/{id}/solve
{ "commentId": "cmt_01J..." }
9. サーバ実装ノート（検証/正規化）
title/body：trim()→長さ検証。body 未指定は "" に正規化。

tags：key重複禁止・種別はスラッグ。

imageKey：presign検査に加えて作成時も再検証。

excerpt：本文から生成（改行→空白、120字、超過時のみ …）。

削除表示：返却時に本文/タイトルを "[削除済み]" へ置換。画像URLは省略/hasImage=false。

リアクション：UNIQUE違反→409、成功は常に204（冪等）。

解決：question スレのみ許可。コメント削除時は 同Txで自動解除。

公開プロフィール付与：JOIN users → faculty_public/year_public が true かつ値ありのみDTOに付与。

カーソル：v/sort/q/snapshotAt/anchor を検証。期限切れ/不整合は 400。
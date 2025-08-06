04b_api_conventions_v1.md — API共通規約（v1・フリーズ）
対象: Base /api/v1。OpenAPI は 04_api_contract_v1.yaml を正とし、本書はその運用規約を定義する。

0. 原則
契約固定：破壊的変更は /api/v2 を新設する（/v1 は互換維持）。

最小権限：閲覧系は認証不要、書込み系は Bearer 必須。

冪等性/再実行安全：クライアントの再送で副作用が増えないようにする。

1. ベース/メディア/文字コード
Base URL: /api/v1

Media Type: application/json; charset=utf-8

時刻: UTC（ISO8601, Z 付き）

2. 認証・認可
方式：Authorization: Bearer <token>

取得：POST /auth/bootstrap（匿名ユーザー + セッション発行）

必須範囲：作成/削除/投票/保存/解決/プロフィール更新/プリサイン
閲覧（一覧・詳細・検索・コメント一覧）は不要。

3. ヘッダ規約
X-Request-Id（全応答に付与）

クライアントから送られた値を尊重、無ければサーバが生成し応答に反映。

X-Snapshot-At（Hot/検索の一覧応答に付与）

並び順固定に用いた基準時刻（ISO8601 UTC）。以降のページングで維持すること。

レート制限系（429時）：Retry-After / X-RateLimit-Limit|Remaining|Reset を付与。

任意: ETag / If-None-Match をGET詳細に限って利用可（変更なしなら 304）。

4. エラー形式（統一）
json
コピーする
編集する
{
  "error": {
    "code": "VALIDATION_ERROR|UNAUTHORIZED|FORBIDDEN|NOT_FOUND|CONFLICT|RATE_LIMITED|INTERNAL",
    "message": "human readable",
    "details": [ { "field":"...", "reason":"...", "required":"..." } ],
    "requestId": "..."
  }
}
例（質問以外で /solve 実行時）：

json
コピーする
編集する
{ "error": {
  "code":"VALIDATION_ERROR",
  "message":"Invalid operation",
  "details":[{"field":"thread.tags","reason":"NOT_APPLICABLE","required":"question"}]
}}
5. バリデーション・正規化
文字列：trim()、制御文字/NULLは拒否。本文はプレーン保存（出力側でサニタイズ）。

長さ：04a の範囲に一致（title 1..60、body 0/1..上限等）。

タグ：key 重複不可。'種別' は question|notice|recruit|chat 固定。

画像：imageKey 形式・拡張子検査（presign時の MIME/size 検査とは別に再検証）。

6. ページング（カーソル）
cursor は base64url(JSON)。必ず "v":1 を含む。

1ページ 20件固定。1リクエストで最大 200件（nextCursor がなくなったら終端）。

Hot/検索は X-Snapshot-At により並びを固定。24時間超えは 400。

タプル比較で重複/欠落を防止：

new: (createdAt DESC, id DESC)

hot: (score DESC, createdAt DESC, id DESC)

comments: (createdAt ASC, id ASC)

7. 並び順・フィルタ
/threads: sort=hot|new、type=（'種別' の値フィルタ）

/search: sort=relevance|new、q（1..100）

コメントは 時系列 ASC 固定（ネスト無し）。

8. レート制限（推奨初期値）
スレ作成：1分/1件（user+IP）

コメント作成：10秒/1件（user+IP）

超過：429 RateLimited（Retry-After 等ヘッダ必須）

9. 冪等性
リアクション：reactions の UNIQUE により冪等（重複は 409 Conflict、成功は常に 204）。

作成系：任意で Idempotency-Key を受理（24h 内は同一処理）。

10. セキュリティ
認証トークンは ハッシュで保存（DB: sessions.token_hash）。

CSRF不要（Authorization ヘッダ運用）。CORS は本番フロントのみ許可。

XSS：プレーン保存、出力時サニタイズ・URLは rel="nofollow noopener"。

S3 直PUT：presign時に MIME/size を検査、DB側でも MIME CHECK（03a）。

11. キャッシュ
一覧/検索：no-store 前提（Hot/スナップショット整合を優先）。

詳細：ETag を付ける場合のみクライアントは If-None-Match を使用可。

12. デプリケーション
互換廃止は Deprecation: true と Sunset ヘッダで告知。最短でも2週間の併存期間。

破壊的変更は /api/v2 を新設し /v1 は並行運用。

13. ロギング/可観測性
すべてのリクエスト/レスポンスに X-Request-Id を相関。

監査ログ（アプリログ）: user_id, action, target, at, ip, ua を 7日保持（08参照）。

14. 受け入れ基準（本書のDoD）
04/04a/03a と整合（ヘッダ・エラー・カーソル仕様が一致）。

追加ルール（solve=質問のみ）はエラーディテールまで明記済み。
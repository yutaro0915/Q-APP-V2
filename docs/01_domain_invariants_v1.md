不変条件（Domain Invariants）v1 — フリーズ版
1) 識別・時刻・可視性
ID：usr_ / thr_ / cmt_ / att_ / rcn_（URL安全な短ID）。

時刻：DB=UTC／表示=JST（相対表記）。

可視性：閲覧は公開。作成/投票/保存/削除はセッション必須。

2) 認証・セッション
統一セッション：user_idを格納するHTTP-only Cookie（SameSite=Lax, TTL≈7日）。

Auth Adapter差替：現行device（端末匿名ID）。将来email_otp/azure_adを追加してもAPI表面は不変。

プロフィール：非公開のみ（学部/学年は任意保存）。
プロフィール項目：faculty（≤50文字）・year（1..10）。公開フラグ：faculty_public/year_public（既定 false）。

取得/表示規約：公開フラグが true の項目のみをスレ/コメントDTOに埋める。ユーザーIDは返さない。

3) スレッド（投稿）
タイトル：必須、1–60全角。

本文：0–2000字。

画像：0/1枚（jpg/png/webp ≤5MB、長辺2048px・EXIF除去済み）。

タグ（固定4キー）：

種別 ∈ {question, notice, recruit, chat}（表示：質問/告知/募集/雑談）

場所（≤50字）、締切（YYYY-MM-DD）、授業コード（≤32字・正規化は将来）

未指定可。重複キー不可。最大4件。

削除：投稿者はいつでも可＝ソフト削除（title/body = "[削除済み]"、検索/ランキング除外、子コメは残す）。復元は管理者のみ。

編集：不可（全項目）。

解決フラグ：solved_comment_id は同スレの未削除コメントに限定。対象コメント削除時は自動でnull。

4) コメント
本文：1–1000字。

画像：0/1枚（投稿と同条件）。

並び：時系列固定（created_at ASC）。ネストなし（フラット）。

削除：投稿者はいつでもソフト削除（body = "[削除済み]"、画像非表示）。

5) リアクション（投票・保存）
スレッド：up と save。

コメント：up のみ。

一意制約：(user_id, target_type, target_id, kind) は唯一（冪等）。

集計：表示用up_count/save_countは遅延一致でOK（真実はreactions）。

6) タイムライン／スコア／熱量
TL並び：
score = (up_count + 0.5*unique_commenters_3h) * exp(- hours_since_created / 12)

新規投稿は5分間の露出保証。削除済みは常に除外。

熱量（0–100）：直近3hの「返信/分」「ユニーク参加者」を正規化合算。5分ごと算出（保存しても返却時計算でも可）。

7) 検索（pg_trgm）
対象：title, body, tags_text(key:value 連結)。

部分一致：pg_trgm + GIN。関連度は similarity(title,q) + 0.2*similarity(body,q) に弱い時減衰。

常に削除済み除外。

8) 画像アップロード（S3）
手順：/uploads/presign → クライアントで縮小&EXIF除去 → S3直PUT → 作成APIにimageKey送付。

S3運用：public-read（日付Dir＋128bitランダムキー）。

表示：TLは16:9サムネ（CSSトリミング）、スレ/コメントは等比。タップで全画面（単枚）。

9) レート制限・安全運用・XSS
作成レート：スレ=1分/件、コメント=10秒/件（user_id+IP）。

本文リンク：自動リンク化（rel="nofollow noopener"）。Markdown禁止。

XSS：プレーン保存＋出力サニタイズ。

通報：無し。緊急時は管理者の強制非表示API。

10) 一貫性・Tx・更新
新規作成：threads.last_activity_at = created_at。コメント作成で常に更新。

解決フラグ：整合性は外部キー相当をアプリで担保（削除時にnull）。

リアクション重複は409で冪等化。

11) エラー規約
400 検証不正／401 未認証／403 権限なし／404 不在／409 重複／429 レート超過。

12) 監査・バックアップ
監査ログ：user_id, action, target, at, ip, ua を7日保持。

RDS：日次スナップショット。画像のバージョニングはv1では無し。


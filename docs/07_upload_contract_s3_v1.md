07_upload_contract_s3_v1.md — 画像アップロード契約（v1・フリーズ）
目的：安全・簡潔・安価に「投稿/コメントごと1枚の画像」を扱うための厳密な運用契約を定義。
依存：RDS PostgreSQL 16（attachments テーブル）、S3（public-read）、/uploads/presign API（04）、DTO（04a）。

0. 方針（要約）
画像は任意（0/1枚）。長辺 2048px にクライアント縮小、EXIF除去、WebP推奨。

S3 は public-read、直PUT。サーバは画像処理しない（サムネ生成なし）。

MIME は image/webp|image/jpeg|image/png、最大 5MB。

DB の attachments(mime,width,height,size,sha256) を満たすため、PUT時に x-amz-meta-* でメタを保存→サーバは HEAD で検証して登録。

1. オブジェクトキー/URL
Key 形式：uploads/{yyyy}/{mm}/{ulid}.{ext}

例：uploads/2025/08/01J6ZQ9B7Y1F5A2K.webp

拡張子は webp|jpg|jpeg|png。

公開URL：https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{key}

v1 は CloudFrontなし（必要になれば将来差し替え可）。

2. フロー（時系列）
（フロント）画像前処理

createImageBitmap → OffscreenCanvas で 長辺2048pxへ縮小。

形式は WebP（品質 0.9 目安。JPEG/PNG でも可）。

ここで EXIF除去（Canvas経由で落ちる）。

（フロント）メタ計算

width,height：前処理後の実寸。

sha256：crypto.subtle.digest('SHA-256', blob) → hex。

size：blob.size（Bytes）。

（フロント）プリサイン要求 POST /uploads/presign

Body: { mime, size }（04/04a 準拠）。

返却: { key, url, headers }（headers は少なくとも Content-Type を含む）。

（フロント）S3へ直PUT

PUT url に 以下ヘッダを付ける：

Content-Type: {mime}（presign付与の値）

x-amz-meta-width: {width}

x-amz-meta-height: {height}

x-amz-meta-sha256: {sha256hex}

※ headers に上記キーが含まれていたら上書きせずに足す。CORS の AllowedHeaders に x-amz-meta-* が必要（後述）。

（フロント）作成API

POST /threads または POST /threads/{id}/comments に imageKey=key を添えて送信（04/04a 準拠）。

（サーバ）登録

HEAD s3://bucket/{key} を実行し、サイズと x-amz-meta-* を取得。

attachments に 同一TxでINSERT（thread_id or comment_id 片側のみ）。

検証：

MIME：image/webp|image/jpeg|image/png（03a の CHECK と一致）

size：1..5MB

width,height：1..8192（念のため）

sha256：64桁 hex

失敗時は投稿全体をロールバックし 400 VALIDATION_ERROR。

API契約（04/04a）は変更しない。headers は任意追加フィールド可なので互換。

3. S3 バケット設定
3.1 CORS（例）
json
コピーする
編集する
[
  {
    "AllowedMethods": ["PUT","GET","HEAD"],
    "AllowedOrigins": ["https://your-frontend.example"],
    "AllowedHeaders": ["Content-Type","x-amz-meta-width","x-amz-meta-height","x-amz-meta-sha256","x-amz-acl"],
    "ExposeHeaders": []
  }
]
3.2 バケットポリシー（public-read）
json
コピーする
編集する
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::YOUR_BUCKET/uploads/*"
  }]
}
PUT権限は presign の署名で限定。ACL は使わずバケットポリシーで公開（S3推奨）。

3.3 暗号化
既定の SSE-S3（AES-256） を有効化（バケットのデフォルト暗号化）。

4. バリデーション（クライアント/サーバ）
項目	クライアント	サーバ
MIME	webp/jpeg/png のみ選択	presign時に拒否、DB CHECK と照合
サイズ	5MB以下	presign時に拒否、HEADの Content-Length で再検証
画像寸法	長辺<=2048に縮小	x-amz-meta-width/height を範囲チェック
EXIF	Canvas経由で除去	（N/A）
ハッシュ	sha256(blob) を x-amz-meta-sha256 に付与	形式検査（将来の重複検知用に保持）

5. エラーと復旧
presign 400：MIME/size不正 → UIで即時メッセージ。

PUT 失敗：ネットワーク/期限切れ（URLはTTL 5分 目安）→ 再度 presign から。

作成API 400：HEADでメタ不整合（例：ヘッダ欠落）→ 再アップしてやり直し。

作成後にS3欠落：表示側で hasImage=false として扱う（v1 不整合は想定外だが、障害時のフォールバック）。

6. セキュリティ/濫用対策
presign TTL：5分（短め）。1ユーザーの presign 発行をレート制限（例：10/min）。

key は サーバが決定（クライアントが名前を選べない）。

直リンクは可能（public-read）だが、key を知らないと推測困難（ULID+年月）。

ウイルス/危険コンテンツ：画像種に限定・EXIF除去でリスク低。違反時は投稿削除と強制非表示で対処（v1）。

7. ガベージ（孤児オブジェクト）
失敗や離脱で DBに紐付かない key が発生し得る。

運用：24時間以上参照なしの uploads/YYYY/MM/* を日次バッチ/手動で削除（ハッカソン中は手動でも可）。

将来：created_at を x-amz-meta-created-at としてPUTし、リスト→判定して削除する簡易スクリプトを用意。

8. 表示規約（フロント）
TL（一覧）：サムネは CSS object-cover × 16:9 の枠で切り取り。

詳細/コメント：等比で表示、タップでフルスクリーン（ImageViewer）。

v1は別解像度生成なし（帯域が問題になれば CloudFront＋変換を導入）。

9. クライアント実装例（擬コード）
ts
コピーする
編集する
// 1) 前処理（縮小→WebP化）
const orig = file; // input type="file"
const img = await createImageBitmap(orig);
const { w, h } = (() => {
  const L = 2048;
  const r = Math.min(L / img.width, L / img.height, 1);
  return { w: Math.round(img.width * r), h: Math.round(img.height * r) };
})();
const canvas = new OffscreenCanvas(w, h);
const ctx = canvas.getContext('2d')!;
ctx.drawImage(img, 0, 0, w, h);
const blob = await canvas.convertToBlob({ type: 'image/webp', quality: 0.9 });

// 2) sha256 計算
const buf = await blob.arrayBuffer();
const hash = await crypto.subtle.digest('SHA-256', buf);
const sha256hex = [...new Uint8Array(hash)].map(b => b.toString(16).padStart(2,'0')).join('');

// 3) presign
const { key, url, headers } = await api('/uploads/presign', {
  mime: blob.type, size: blob.size
}, true);

// 4) PUT
await fetch(url, {
  method: 'PUT',
  headers: {
    ...headers, // Content-Type はここに入っている
    'x-amz-meta-width': String(w),
    'x-amz-meta-height': String(h),
    'x-amz-meta-sha256': sha256hex
  },
  body: blob
});

// 5) 作成API
await api('/threads', {
  title, body, tags, imageKey: key
}, true);
10. サーバ実装メモ（検証と登録）
POST /uploads/presign：

入力：mime ∈ {webp,jpeg,png}、size ≤ 5MB。

出力：{key,url,headers:{'Content-Type': mime}}。TTL=300s。

POST /threads|/comments（imageKey あり）で：

HEAD：Content-Length と x-amz-meta-width|height|sha256 を取得。

検証：長さ/値の形式。

登録：attachments へ INSERT（thread_id or comment_id をセット）。

Tx：投稿INSERT/コメントINSERTと 同一トランザクション。

11. DoD（この文書の受け入れ条件）
04/04a のスキーマを変更せずに、attachments の必須列（03a）を満たす保存経路が明文化されている。

バケット設定（CORS/ポリシー）とクライアント/サーバ双方の具体手順が示されている。

失敗時のエラー処理とガベージ運用が定義されている。


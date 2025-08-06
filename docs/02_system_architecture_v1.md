02_system_architecture_v1.md — システム構成（v1）
目的：最小コストで“動く”学内SNSを短期で安定運用するための構成・責務・接続・運用規約を固定する。
対象：Next.js（Front）／FastAPI（API）／RDS PostgreSQL 16／S3／App Runner（AWS）

0. スコープと原則
スコープ：Webアプリ（フロント/バックエンド）、DB、ストレージ、CI/CD、監視、セキュリティ境界。

原則

単純さ最優先（処理はAPIへ、表示はFrontへ）

ステートレス（セッションはDBで管理）

公開読み／認証書き込み（閲覧は匿名OK、作成系はBearer必須）

契約駆動（01/03/04に従う。破壊変更は/v2）

1. 全体構成（概要）
Frontend：Next.js 14（App Router, SSR+CSR, Tailwind+shadcn/ui）

Backend：FastAPI（Uvicorn, Python 3.11, asyncpg/SQLAlchemy Core）

DB：Amazon RDS for PostgreSQL 16（拡張：pg_trgm）

Object Storage：Amazon S3（public-read、presigned PUT）

デプロイ：AWS App Runner（Front / API 各1サービス）

ネットワーク：API→RDS は VPC Connector 経由（Private Subnet）

ログ/監視：CloudWatch Logs（app/access）／App Runner & RDS メトリクス

CDN：なし（v1）。必要になれば CloudFront を将来導入

2. 責務分割
Front（Next.js）
画面レンダリング（単一カラム）／ナビゲーション

初回 SSR 取得（TL/検索/スレ詳細）

画像縮小(長辺2048)・EXIF除去 → S3直PUT（presign利用）

作成/削除/投票/解決/プロフィール更新は CSR fetch（Bearer 必須）

エラー表示（ErrorResponse→トースト/バナー）、相対時刻、画像ビューア

API（FastAPI）
認証（/auth/bootstrap → セッショントークン）／認可

バリデーション（DTO 04a 準拠）／レート制限（スレ1/min、コメ10s）

ソフト削除・解決フラグ・リアクション冪等

カーソルページング＋snapshotAt（Hot/検索の順序固定）

検索（pg_trgm 類似度 + 弱い時間減衰）

プロフィール（学部/学年＋公開フラグの取得/更新）

RDS（PostgreSQL 16）
恒久データ（users/credentials/sessions/threads/comments/tags/attachments/reactions）

インデックス：pg_trgm、未削除部分Index、JOIN最適化

バックアップ：日次スナップショット

S3
バケット：public-read（キー例：uploads/YYYY/MM/uuid.webp）

CORS：PUT/GET、本番フロントのみ許可

presign は API が発行、MIME/size を再検証

3. ネットワーク/セキュリティ境界
Front（Public） → API（Public） → VPC Connector → RDS（Private）

S3 は クライアントから直PUT（presign URL）。GET は公開。

CORS：APIは本番フロント1ドメインのみ許可（開発は .env で追加）

TLS：App Runner / 独自ドメインの証明書（Front, API）

権限：自身の投稿/コメントのみ削除・解決可。管理者は強制非表示可（通報機能はv1無し）

4. 認証/セッション
方式：Bearer（Authorization: Bearer <token>）

発行：POST /auth/bootstrap（端末匿名ID）→ { userId, token, expiresAt }

保存：sessions.token_hash = sha256(token)

TTL：7日。失効→401

将来：Email OTP / Azure AD をアダプタ追加（API表面は不変）

5. データフロー（主要シーケンス）
5.1 画像アップロード
Front → API POST /uploads/presign {mime,size}

API → key,url,headers 返却

Front → S3直PUT（縮小WebP＋EXIF除去）

Front → API POST /threads|/comments { imageKey:key, ... }

5.2 TL（Hot, snapshot）
Front SSR → API GET /threads?sort=hot（1ページ目）

API → X-Snapshot-At ヘッダと nextCursor 返却

Front CSR → 同 snapshotAt で ?cursor=... を連続取得（最大200件）

5.3 検索（relevance）
similarity(title,q) + 0.2*similarity(body,q) + 0.2*time_decay(24h@snapshotAt)

6. 非機能（SLO/スケール/運用）
SLO：GET /threads p95 < 400ms（20件）／FCP < 2.5s

App Runner：最小インスタンス 1、オートスケール有効

DBプール：MAX 10–20（同時接続を抑制）

バックアップ：RDS 日次スナップショット（保持7–14日）

監査ログ：user_id, action, target, at, ip, ua（7日保持／アプリログ）

7. バージョニング/契約
API Base：/api/v1（破壊的変更は /api/v2 を新設）

ドキュメント：*_v1.* を上書きしない。破壊変更は v2ファイルを追加

カーソル/スナップショット：04b の規約を必ず遵守

8. 環境/設定
8.1 API（env）
ini
コピーする
編集する
DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DB
DB_POOL_MIN=1
DB_POOL_MAX=10
SESSION_TOKEN_SECRET=...
SESSION_TTL_HOURS=168
S3_BUCKET=...
S3_REGION=ap-northeast-1
S3_PUBLIC_BASE=https://{bucket}.s3.{region}.amazonaws.com
CORS_ORIGINS=https://your-frontend.example
8.2 Front（env）
ini
コピーする
編集する
NEXT_PUBLIC_API_BASE=/api/v1
9. セキュリティ対策まとめ
XSS：本文/タイトルはプレーン保存、出力時サニタイズ。URL自動リンク化（rel="nofollow noopener"）

CSRF：Bearer ヘッダ運用のため不要

S3：presign 時に MIME/size を検査。DB側でも MIME を CHECK（03a）

RDS：API SG のみ許可。パスワードは Secrets Manager（任意）

10. 既知のトレードオフ
reactions.target_id／threads.solved_comment_id：物理FKなし（シンプルさ優先、アプリで整合）

タグ全文検索：v1 は JOIN／必要時に tags_text + GIN へ昇格（03参照）

画像CDN：v1は直S3／必要時に CloudFront を追加

11. 運用フロー（要点）
CI/CD：main への push で ECR ビルド → App Runner 更新（09参照）

障害時：X-Request-Id でトレース、RDS ロールバックはスナップショットから

レート超過：429（Retry-After 等ヘッダ）をUIで提示

12. 完了条件（この文書のDoD）
01/03/04/04a/04b/05/06/07/08/09 と矛盾がない（最終確認済み）

破壊的変更は /api/v2 を作る運用が明記されている


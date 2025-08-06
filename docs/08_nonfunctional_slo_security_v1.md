08_nonfunctional_slo_security_v1.md — 非機能 / SLO / セキュリティ（v1・フリーズ）
参照：02（アーキテクチャ）、03/03a（ERD/DDL）、04/04a/04b（API/DTO/規約）、05/06（設計）、07（アップロード）
前提：掲示板=非同期。リアルタイム通信なし（v1はポーリングのみ）。

0. 目的
v1を短期構築しつつ、最低限の性能・可用性・セキュリティを担保するための数値目標と運用規約を固定。

1. SLO（Service Level Objective）
1.1 可用性
月間可用性 ≥ 99.9%（月あたり < 43分 のダウンタイム）。

対象：API（/api/v1） と フロントSSR。S3 は除外（クラウド依存）。

1.2 レイテンシ（p95）
エンドポイント	目標 (p95)	条件
GET `/threads?sort=hot	new`（20件）	< 400ms
GET /search（20件）	< 600ms	pg_trgm 類似度
GET /threads/{id}	< 300ms	JOIN users, tags
GET /threads/{id}/comments（20件）	< 350ms	ASC + 部分Index
POST /threads	< 500ms	tags/attachments 同Tx
POST /comments	< 450ms	last_activity_at 更新含む
POST /uploads/presign	< 150ms	署名発行のみ
POST /threads/{id}/reactions, /comments/{id}/reactions	< 200ms	冪等 INSERT

1.3 スループット（想定キャパ）
初期：App Runner 1インスタンス（0.5–1 vCPU / 1–2GB）で RPS 30–60 目安。

ピーク時：水平スケールで RPS >150 まで引き上げ可能（DB接続を20以下で制御）。

1.4 エラーバジェット
「5xx 率」月間 < 0.5%。超過時は新機能停止→安定化優先。

2. 性能設計 & キャパ計画
2.1 DB・インデックス（03a 準拠）
threads(title/body) GIN gin_trgm_ops

部分Index：未削除のみ（threads/comments）

tags(key,value) BTree

連続ページング：タプル比較（安定順序）

2.2 コネクション・プール
API→RDS：MAX_CONNECTIONS = 10–20（App Runner インスタンスあたり）

RDS：t4g.small 目安（プロトタイプ）。Performance Insights で監視。

2.3 キャッシュ/整合
一覧・検索：cache-control: no-store（スナップショット整合重視）

詳細：必要に応じ ETag/If-None-Match（変更なしは 304）

画像：S3 直GET（ブラウザキャッシュ任せ）

2.4 ポーリング（リアルタイム代替）
スレ詳細の新規コメント：10–15秒 間隔で /comments 続き取得

通知バッジ（将来）：30–60秒 間隔（v1では最小限）

3. レート制限 & 乱用対策
スレ作成：1分/1件（user+IP）

コメント：10秒/1件（user+IP）

presign 発行：10/min（user）

429時：Retry-After / X-RateLimit-* を必ず返却（04b）

DoS緩和：App Runnerの自動スケール + WebACL（将来、必要なら）

4. セキュリティ（技術的対策）
4.1 認証/セッション
Bearer（/auth/bootstrap）。DB保存は token のハッシュ（sessions.token_hash UNIQUE）。

TTL：7日。失効→401。

4.2 権限
自分のスレ/コメントのみ削除可。解決フラグはスレ主のみ。

質問以外での /solve は 400 NOT_APPLICABLE（04/04a/04b）。

4.3 入出力
本文はプレーン保存。出力時サニタイズ（リンクは rel="nofollow noopener"）。

画像：MIME/サイズを presign 時検査、DB側でも CHECK（03a）。

4.4 CORS/CSRF
CORS：本番フロントのみ許可（開発は env で追加）。

CSRF：不要（Authorization ヘッダ運用）。

4.5 S3
public-read（GETのみ公開、PUTは presign）。

CORS：PUT/GET/HEAD + x-amz-meta-*（07 参照）。

署名TTL：5分。

5. プライバシー & 個人情報
実名やメール等は扱わない（v1）。

プロフィールは任意（faculty/year）＋公開フラグで制御。

ログの IP/UA は7日保持（運用監査目的のみ）。

6. ログ / 監査 / 可観測性
X-Request-Id：全リクエストに相関（04b）。レスポンスにも返却。

アプリ監査ログ（CloudWatch Logs）

user_id, action, target, at, ip, ua（7日保持）

例：THREAD_CREATE, COMMENT_DELETE, REACTION_ADD, SOLVE_SET/CLEAR

メトリクス

App Runner：CPU/メモリ/リクエスト数

RDS：CPU/接続数/バッファヒット/スロークエリ

アラート（最小）

5xx 率 > 1%（5分平均）

RDS 接続使用率 > 80%（5分連続）

レイテンシ p95 上限超（各主要GET/POSTで）

7. バックアップ / 復旧
RDS：日次スナップショット（保持 7–14日）。

画像（S3）：バージョニングなし（v1）。違反や誤アップはアプリ側で非表示対応。

復旧手順（要点）

事故発生 → 時刻を特定

RDS をスナップショットから新インスタンスへ復元

API の DATABASE_URL を切替、整合確認

必要であれば S3 の当該 prefix を棚卸し

8. デプロイ / ロールアウト（概要）
CI/CD：main への push → ECR ビルド → App Runner 更新（09 参照）

ロールアウト：段階的（%切替）までは不要。失敗時は前タグへロールバック。

ヘルスチェック：API /auth/session（200/401で合格）

9. 非機能テスト計画（最低限）
9.1 負荷テスト
シナリオ：

GET /threads 50rps、/search 10rps、POST /comments 5rps（10分）

合格基準：全リクエスト p95 が SLO 内、5xx 率 < 0.5%

9.2 回帰テスト（カーソル）
100件以上で 2ページ目の重複なし、最終ページで nextCursor=null。

9.3 故障注入（簡易）
RDS 接続エラーを模擬 → API が 5xx を返しつつログに requestId を出すこと。

S3 PUT 期限切れ → presign 再発行で回復。

10. アクセシビリティ / UX 非機能
キーボード操作：主要操作（投稿、保存、いいね、解決）に aria-label。

読上げ：重要バッジ（解決済み）はラベル付与。

レスポンシブ：単一カラム、幅 680–760px（PC）中心。

11. データ保持ポリシー
deleted_at によりソフト削除。

削除本文/タイトルは返却時に "[削除済み]" へ置換（03/04a）。

監査ログ（IP/UA）は 7日で自動ローテーション（運用で管理）。

12. 既知のリスクと回避策
検索負荷増：タグ JOIN が増える → v1.1 で tags_text + GIN を導入。

画像帯域：モバイルで増加 → 将来 CloudFront + 変換（WebP/サイズ別）を検討。

ソフト削除の肥大：部分Indexで回避、必要に応じアーカイブジョブを導入。

13. 本書のDoD
SLO/セキュリティ/運用の数値目標が定義され、他ドキュメントと矛盾しない。

v1ではリアルタイム不採用、ポーリング/ETag運用を明文化。

監視・アラート・バックアップの最低限が示されている。


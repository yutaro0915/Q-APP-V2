05_backend_design_fastapi_v1.md — バックエンド設計（v1）
Stack: FastAPI + Uvicorn（Python 3.11） / PostgreSQL 16 / S3
前提：Bearer 認証、カーソルページング、pg_trgm、ソフト削除、画像は各1枚

1. レイヤ構成 & 責務
bash
コピーする
編集する
api/app/
  main.py                     # 起動/ミドルウェア/CORS/例外ハンドラ
  deps/auth.py                # Bearer 検証（user_id 解決）
  routers/                    # HTTP I/O（薄い）
    auth.py uploads.py threads.py comments.py reactions.py search.py profile.py
  services/                   # ドメインロジック（ここが主役）
    auth_service.py upload_service.py thread_service.py comment_service.py
    reaction_service.py search_service.py profile_service.py cursor.py hot.py
  repos/                      # SQL 実行・トランザクション境界
    users_repo.py threads_repo.py comments_repo.py tags_repo.py reactions_repo.py attachments_repo.py sessions_repo.py
  db/
    base.py                   # asyncpg / SQLAlchemy Core 接続・Txユーティリティ
    models.py                 # テーブルメタ（Core）
  schemas/
    dto.py                    # Pydantic DTO（04a と一致）
  util/
    idgen.py                  # prefix_ULID 生成
    time.py log.py errors.py  # UTC/ログ/例外→ErrorResponse
Routers：入力検証→サービス呼び出し→レスポンス成形だけ。

Services：ルール実装（検証、Tx制御、派生値更新、S3/Pg連携）。

Repos：純SQL（Core で発行）。ビジネス判断は持たない。

2. Cross-cutting
認証：Authorization: Bearer <token> → sessions.token_hash 照合 → user_id。

CORS：本番フロント1ドメインのみ許可（開発は .env で追加）。

バリデーション：Pydantic（schemas/dto.py は 04a と一致）。

エラー：errors.py で HTTPException を 統一 ErrorResponse に変換。

レート制限：

スレ作成：直近1分に自分の threads 件数で判定（user_id+IP）。

コメント：直近10秒に自分の comments 件数。

429時、Retry-After / X-RateLimit-* ヘッダ付与。

ログ/トレース：X-Request-Id を受け取り or 生成し全ログへ出力。

3. 主要サービス API（関数シグネチャ）
py
コピーする
編集する
# auth_service.py
async def bootstrap(device_secret: str | None) -> tuple[str, str, datetime]: ...
async def get_session(user_id: str) -> str: ...
async def logout(user_id: str, token_hash: str) -> None: ...

# profile_service.py
async def get_my_profile(user_id: str) -> MyProfileDTO: ...
async def update_my_profile(user_id: str, dto: UpdateMyProfileDTO) -> None: ...

# upload_service.py
async def create_presign(user_id: str, mime: str, size: int) -> PresignDTO: ...

# thread_service.py
async def create_thread(user_id: str, dto: CreateThreadDTO) -> CreatedDTO: ...
async def list_threads(sort: Literal['hot','new'], ttype: str | None,
                       cursor: Cursor | None) -> Paginated[ThreadCardDTO]: ...
async def get_thread(thread_id: str) -> ThreadDetailDTO: ...
async def delete_thread(user_id: str, thread_id: str) -> None: ...
async def solve_comment(user_id: str, thread_id: str, comment_id: str | None) -> None: ...

# comment_service.py
async def list_comments(thread_id: str, cursor: Cursor | None) -> Paginated[CommentDTO]: ...
async def create_comment(user_id: str, thread_id: str, dto: CreateCommentDTO) -> CreatedDTO: ...
async def delete_comment(user_id: str, comment_id: str) -> None: ...

# reaction_service.py
async def react_thread(user_id: str, thread_id: str, kind: Literal['up','save']) -> None: ...
async def react_comment(user_id: str, comment_id: str, kind: Literal['up']) -> None: ...

# search_service.py
async def search(q: str, sort: Literal['relevance','new'], cursor: Cursor | None) -> Paginated[ThreadCardDTO]: ...
4. トランザクションと副作用
スレ作成：threads INSERT → tags INSERT ≤4 → attachments(任意) を 同一Tx。

コメント作成：comments INSERT → threads.last_activity_at = now() を 同一Tx。

リアクション：reactions INSERT ON CONFLICT DO NOTHING → 影響1行なら up_count/save_count インクリメント（同Tx）。

解決：対象コメントの同一スレ/未削除を検証→solved_comment_id 更新（解除は NULL）。

削除：ソフト削除（deleted_at セット、返却時に本文/タイトルを "[削除済み]" に置換）。

コメント削除 → 同Txで threads.solved_comment_id が当該なら NULL に。

5. Hot/検索スコア & カーソル
Hot：(up_count + 0.5*uniq_commenters_3h) * exp(-hours_since_created/12)

クエリ時算出 or 5分以上経過時のみ遅延更新。

検索：similarity(title,q) + 0.2*similarity(body,q) + 弱い時間減衰(24h)。

カーソル：cursor.py に実装。base64url(JSON)。snapshotAt で順序固定（24h）。

6. プロフィール公開付与ロジック
スレ/コメント取得の際に JOIN users u：

author_faculty = CASE WHEN u.faculty_public AND u.faculty IS NOT NULL THEN u.faculty END

author_year = CASE WHEN u.year_public AND u.year IS NOT NULL THEN u.year END

サービス層で {authorAffiliation: null|{faculty,year}} に整形。

7. 代表クエリ断片（擬SQL）
TL（hot）一覧 20件

sql
コピーする
編集する
WITH uc AS (
  SELECT thread_id, COUNT(DISTINCT author_id) AS cnt
  FROM comments
  WHERE created_at > :snapshotAt - interval '3 hours'
  GROUP BY thread_id
)
SELECT t.id, t.title, t.body, t.up_count, t.save_count,
       COALESCE(uc.cnt,0) AS uniq3h,
       ((t.up_count + 0.5*COALESCE(uc.cnt,0)) *
        EXP(-EXTRACT(EPOCH FROM (:snapshotAt - t.created_at))/43200)) AS hot,
       t.created_at, t.last_activity_at,
       CASE WHEN u.faculty_public AND u.faculty IS NOT NULL THEN u.faculty END AS author_faculty,
       CASE WHEN u.year_public AND u.year IS NOT NULL THEN u.year END AS author_year
FROM threads t
JOIN users u ON u.id = t.author_id
LEFT JOIN uc ON uc.thread_id = t.id
WHERE t.deleted_at IS NULL
  AND (:type IS NULL OR EXISTS (SELECT 1 FROM tags g WHERE g.thread_id=t.id AND g.key='種別' AND g.value=:type))
  AND ( :anchor IS NULL OR (hot, t.created_at, t.id) < (:a_hot, :a_created_at, :a_id) )
ORDER BY hot DESC, t.created_at DESC, t.id DESC
LIMIT 20;
検索（relevance）：03 の記載に準拠。

8. 例外/エラー変換
例）検証失敗 → VALIDATION_ERROR、権限なし → FORBIDDEN、重複投票 → CONFLICT、等を ErrorResponse へ変換。

すべてに X-Request-Id を返し、ログに同IDを出力。

9. 設定（env） & プール
ini
コピーする
編集する
DATABASE_URL=postgres://...
DB_POOL_MIN=1
DB_POOL_MAX=10
SESSION_TOKEN_SECRET=...
SESSION_TTL_HOURS=168
S3_BUCKET=...
S3_REGION=ap-northeast-1
S3_PUBLIC_BASE=https://{bucket}.s3.{region}.amazonaws.com
CORS_ORIGINS=https://front.example
DB接続：App Runner 常駐前提で MAX=10–20。

時刻：APIは常に UTC、now() 使用統一。

10. テスト観点（最低限）
作成/削除/解決のTx整合（削除→解決NULL）

リアクション二重禁止（409）

TL/検索のカーソル（2ページ目が1ページ目と重複しない）

プロフィール公開切替の反映（表示が即時変わる）

画像：presign → PUT → 作成API受理（MIME/size ガード）


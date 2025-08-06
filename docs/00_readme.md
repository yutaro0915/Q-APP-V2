# 九大学内SNS v1 詳細設計（フリーズ版）



---

## 0. 要約（決定の再掲）

* **構成**：Frontend=Next.js、Backend=FastAPI、DB=RDS PostgreSQL16（`pg_trgm`）、画像=S3（public-read）、デプロイ=App Runner×2。
* **UX**：単一カラム。TL（薄いカード・1行プレビュー）／スレ（時系列コメント）。
* **匿名**：端末匿名ID→Bearer セッション（将来 Email OTP / Azure AD 追加可）。
* **機能**：スレ/コメント（**画像は各1枚**）、Up/保存（スレ）、Up（コメント）、解決フラグ、検索（pg\_trgm）、Hot並び、削除は**いつでもソフト削除**。
* **通報**：なし。自動ガードはレート制限のみ。

---

## 1. システム構成

* **Frontend**：Next.js 14（App Router、Tailwind + shadcn/ui）
* **Backend**：FastAPI（Python 3.11, Uvicorn, asyncpg/SQLAlchemy Core）
* **DB**：Amazon RDS for PostgreSQL 16（拡張：`pg_trgm`）
* **Storage**：S3（public-read, presigned PUT）
* **Auth**：プラガブル（v0: device / v1+: email\_otp / v2+: azure\_ad）
* **Deploy**：AWS App Runner（front/api 各1サービス）、VPC 接続で RDS 私設アクセス
* **監視/ログ**：CloudWatch Logs（アプリログ）／RDS 日次スナップショット

---

## 2. 不変条件（Domain Invariants）

**ID/時間/可視性**

* ID：`usr_ / thr_ / cmt_ / att_ / rcn_`（URL安全短ID）
* DB=UTC、表示=JST（相対表記）
* 閲覧は公開。**作成/投票/保存/削除はセッション必須**

**認証/セッション**

* `POST /auth/bootstrap` で匿名ユーザー作成＋セッショントークン（Bearer）
* 将来の OTP / Azure AD 追加時も **API 表面は不変**

**スレッド**

* タイトル必須（1–60 全角）／本文 0–2000／**画像 0/1 枚**
* タグ：`種別(question|notice|recruit|chat)`・`場所`・`締切(YYYY-MM-DD)`・`授業コード`（任意）
* **削除はいつでも**ソフト削除（`"[削除済み]"` 表示、検索/Hot から除外）／**編集不可**
* 解決フラグ：スレ主のみ／対象コメント削除で **自動解除**

**コメント**

* 本文 1–1000／**画像 0/1 枚**／**時系列固定**／ネストなし
* いつでもソフト削除（本文置換・画像非表示）

**リアクション**

* スレ：`up`・`save`／コメント：`up`
* 一意制約：`(user_id,target_type,target_id,kind)`
* 集計値は遅延一致でOK（真実は `reactions`）

**TL/Hot/熱量**

* `score = (up + 0.5*unique_commenters_3h) * exp(-hours/12)`＋**新規5分ブースト**
* 熱量 0–100（直近3hの 返信/分 と ユニーク参加者）

**検索**

* pg\_trgm 部分一致（`title`,`body`,`tags_text`）／`similarity(title,q) + 0.2*similarity(body,q)` に弱い時減衰

**画像アップロード**

* `/uploads/presign` → **クライアントで縮小(長辺2048) & EXIF除去** → S3 直 PUT → `imageKey` を作成 API に渡す
* TL は**16:9 サムネ**（CSSトリミング）、スレ/コメントは等比、タップで全画面

**レート/XSS**

* スレ：1分/件、コメント：10秒/件（user\_id+IP）
* Markdown不可、URL自動リンク化（`rel="nofollow noopener"`）、出力サニタイズ

**エラー規約**

* 400/401/403/404/409/429（詳細は API セクション）

---

## 3. データモデル（ERD/DDL 抜粋）

**ERD（テキスト）**

```
users ──< credentials
users ──< sessions
users ──< threads ──< comments
threads ──< tags
threads ──< attachments   comments ──< attachments
users ──< reactions (target: thread|comment)
```

**DDL（主要テーブル）**

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE users (
  id TEXT PRIMARY KEY,
  role TEXT NOT NULL DEFAULT 'student',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE credentials (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  provider TEXT NOT NULL CHECK (provider IN ('device','email_otp','azure_ad')),
  subject TEXT NOT NULL,
  secret_hash TEXT,
  is_primary BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_used_at TIMESTAMPTZ,
  UNIQUE (provider, subject)
);

CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  token_hash TEXT NOT NULL UNIQUE,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE threads (
  id TEXT PRIMARY KEY,
  author_id TEXT NOT NULL REFERENCES users(id),
  title TEXT NOT NULL,
  body  TEXT NOT NULL,
  up_count   INTEGER NOT NULL DEFAULT 0,
  save_count INTEGER NOT NULL DEFAULT 0,
  solved_comment_id TEXT NULL, -- 物理FKは貼らずアプリで整合
  heat INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_activity_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);

CREATE TABLE comments (
  id TEXT PRIMARY KEY,
  thread_id TEXT NOT NULL REFERENCES threads(id),
  author_id TEXT NOT NULL REFERENCES users(id),
  body TEXT NOT NULL,
  up_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ
);

CREATE TABLE attachments (
  id TEXT PRIMARY KEY,
  thread_id TEXT REFERENCES threads(id),
  comment_id TEXT REFERENCES comments(id),
  key TEXT NOT NULL,
  mime TEXT NOT NULL,
  width INTEGER NOT NULL,
  height INTEGER NOT NULL,
  size INTEGER NOT NULL,
  sha256 TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK ((thread_id IS NOT NULL) <> (comment_id IS NOT NULL))
);

CREATE TABLE tags (
  thread_id TEXT NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
  key TEXT NOT NULL CHECK (key IN ('種別','場所','締切','授業コード')),
  value TEXT NOT NULL,
  PRIMARY KEY (thread_id, key)
);

CREATE TABLE reactions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  target_type TEXT NOT NULL CHECK (target_type IN ('thread','comment')),
  target_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('up','save')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, target_type, target_id, kind)
);

CREATE INDEX idx_threads_title_trgm ON threads USING gin (title gin_trgm_ops);
CREATE INDEX idx_threads_body_trgm  ON threads USING gin (body  gin_trgm_ops);
CREATE INDEX idx_threads_last_activity ON threads(last_activity_at);
```

---

## 4. API コントラクト（主要 12 本）

**共通**：認証は **Bearer**（`Authorization: Bearer <token>`）。未認証 401。
**エラー**：400(検証), 401(未認証), 403(権限), 404(不在/削除), 409(重複), 429(レート)。

### 4.1 認証・アップロード

* `POST /auth/bootstrap` → `{ userId, token, expiresAt }`
  *端末匿名IDでユーザー作成＆セッション発行*
* `GET /auth/session` → `{ userId }` / 401
* `DELETE /auth/session` → `{ ok:true }`
* `POST /uploads/presign`

  * Req `{ mime: 'image/webp'|'image/jpeg'|'image/png', size: number }`
  * Res `{ key, url, headers: {'Content-Type': string} }`

### 4.2 スレッド

* `POST /threads`

  * Req `{ title(1..60), body(0..2000), tags?: Tag[], imageKey?: string }`
  * Res `{ id, createdAt }`
* `GET /threads?sort=hot|new&type=question|notice|recruit|chat&page=1`

  * Res `{ items: ThreadCard[], nextPage?: number }`
* `GET /threads/{id}`

  * Res `{ thread: ThreadDetail, comments: Comment[] }`
* `DELETE /threads/{id}` → `{ ok:true }`

### 4.3 コメント

* `POST /threads/{id}/comments`

  * Req `{ body(1..1000), imageKey?: string }`
  * Res `{ id, createdAt }`
* `DELETE /comments/{id}` → `{ ok:true }`

### 4.4 リアクション/解決

* `POST /threads/{id}/reactions` (body:`{kind:'up'|'save'}`)
* `POST /comments/{id}/reactions` (body:`{kind:'up'}`)
* `POST /threads/{id}/solve` (body:`{commentId:string|null}`)

### 4.5 検索

* `GET /search?q=...&sort=relevance|new&page=1`

  * Res `{ items: ThreadCard[], nextPage?: number }`

**DTO（抜粋）**

```json
// ThreadCard
{
  "id": "thr_xxx", "title": "…", "excerpt": "…",
  "tags": [{"key":"種別","value":"質問"},{"key":"締切","value":"2025-08-10"}],
  "heat": 72, "replies": 12, "saves": 4,
  "createdAt": "2025-08-06T05:12:00Z", "lastReplyAt": "2025-08-06T08:02:00Z",
  "hasImage": true, "imageThumbUrl": "https://s3…/thumb.webp"
}
```

---

## 5. バックエンド設計（FastAPI）

**ディレクトリ**

```
api/app/
  main.py
  deps/auth.py                  # Bearer検証
  routers/
    auth.py uploads.py threads.py comments.py reactions.py search.py
  services/
    auth_service.py thread_service.py comment_service.py reaction_service.py search_service.py upload_service.py
  repos/
    users_repo.py threads_repo.py comments_repo.py reactions_repo.py tags_repo.py attachments_repo.py
  db/
    base.py models.py migrations/
  schemas/
    common.py  # Pydantic DTO
```

**サービス層シグネチャ（抜粋）**

```py
async def create_thread(user_id: str, dto: CreateThreadDTO) -> ThreadId
async def list_threads(sort: Literal['hot','new'], ttype: Optional[str], page: int) -> List[ThreadCardDTO]
async def get_thread(thread_id: str) -> ThreadDetailDTO
async def delete_thread(user_id: str, thread_id: str) -> None
async def add_comment(user_id: str, thread_id: str, dto: CreateCommentDTO) -> CommentId
async def react(user_id: str, target: Target, kind: Literal['up','save']) -> None
async def solve_comment(user_id: str, thread_id: str, comment_id: Optional[str]) -> None
```

**Hot/熱量（クエリ時 or 遅延更新）**

* Hot = up\_count + 0.5\*直近3hユニーク参加者 × 時間減衰
* 5分以上経過時にのみ `threads.heat` 更新でもOK（遅延一致）

**検索（pg\_trgm）**

* `ILIKE` + `similarity()`、タイトル重み 1.0、本文 0.2、弱い時減衰

**レート制限**

* 直近 1分/10秒 を `created_at` 集計で判定（user\_id+IP）

---

## 6. フロント設計（Next.js）

**ルーティング**

```
/               # TL（Hot / New 切替） 検索バー
/search         # 検索モード（?q=…）  URLは分離
/thread/[id]    # スレ詳細（コメント時系列）
```

**コンポーネント（Props）**

```
ThreadCard.tsx {
  id, title, excerpt, tags, heat, replies, saves,
  createdAt, lastReplyAt?, hasImage, imageThumbUrl?, liked, saved
}
ThreadList.tsx { items, onLoadMore? }
ThreadView.tsx { thread: ThreadDetailDTO, comments: CommentDTO[] }
CommentItem.tsx { id, body, createdAt, upCount, hasImage, imageUrl, liked }
HeatChip.tsx { value: number } (0..100)
TagChips.tsx { tags }
ImageViewer.tsx { src }
NewThreadForm.tsx  # タイトル必須、タグ、画像1枚（ブラウザ縮小→presign→PUT）
NewCommentForm.tsx # 本文、画像1枚（同上）
```

**データ取得**

* TL/検索：SSR で初回 20 件 → クライアント追い読み
* スレ詳細：SSR（`no-store` で都度）

---

## 7. 画像アップロード契約（S3）

**フロー**

1. `POST /uploads/presign`（mime/size バリデ）
2. 返却 `url, headers, key` で **S3 に直 PUT**
3. `imageKey` を `POST /threads` / `POST /comments` に渡す

**ブラウザ処理**

* canvas で長辺 2048px へ縮小、**webp** 優先、EXIF 除去
* TL は CSS で **16:9 サムネ**、スレ/コメントは等比、**タップで全画面**（単枚表示）

**S3 CORS（例）**

```json
[
  {"AllowedHeaders":["*"],"AllowedMethods":["PUT","GET"],"AllowedOrigins":["https://your-frontend.example"],"ExposeHeaders":[]}
]
```

---

## 8. 非機能/SLO・セキュリティ

* **SLO**：p95 API（GET /threads 20件）< **400ms**／モバイル FCP < **2.5s**
* **XSS**：プレーン保存・出力サニタイズ／URL自動リンク化（`nofollow noopener`）／Markdown不可
* **バックアップ**：RDS 日次スナップショット
* **監査**：`user_id, action, target, at, ip, ua` を 7 日保持
* **S3**：public-read の旨をアップロード UI に明記

---

## 9. デプロイ/設定

**環境変数（API）**

```
DATABASE_URL=postgres://...
SESSION_TOKEN_SECRET=...
SESSION_TTL_HOURS=168
S3_BUCKET=...
S3_REGION=ap-northeast-1
S3_PUBLIC_BASE=https://{bucket}.s3.{region}.amazonaws.com
```

**App Runner**

* front/api 各サービスを作成（api は VPC 接続で RDS に私設アクセス）
* CloudWatch Logs 有効化

---

## 10. フェーズ設計（各段階で“動く”）

**Phase 1 — 核（スレ作成/閲覧/削除）**
DoD：匿名ログイン→スレ作成→TL表示→詳細閲覧→削除が一連で通る（新着順）

**Phase 2 — コメント/リアクション/解決**
DoD：コメント投稿→時系列表示、スレ up/save と コメント up が二重不可、解決ピン

**Phase 3 — 画像/検索/タグ拡張**
DoD：画像付投稿（TL 16:9 サムネ/全画面表示）、pg\_trgm 検索、場所/締切/授業コードタグ

**Phase 4 — Hot/熱量/UX**
DoD：TL が Hot に切替、熱量表示、最新返信 1 行プレビュー

---

## 11. Issue テンプレ（コピペで使う）

```
# [EPIC] Phase {N}: {名前}
目的 / 完成条件（DoD）
影響範囲: DB | API | UI | Infra
関連不変条件: INV-...

## Issue: {動詞ではじめる}
### 背景
（1-2文）
### 仕様（契約）
- 入力（型/制約）
- 出力（型/制約）
- 状態変化（DB/副作用）
- エラー（400/401/403/404/409/429）
### 実装タスク
- [ ] マイグレ（DDL）
- [ ] レポ/サービス
- [ ] ルータ/エンドポイント
- [ ] フロント受け渡し
- [ ] ログ/監査
### 影響範囲
（DB/API/UI の変更点）
### テスト
- 正常系（3）／異常系（3）
### DoD
（手動手順 or スクショ要件）
```

---


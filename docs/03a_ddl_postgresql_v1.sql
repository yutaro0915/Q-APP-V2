-- /docs/03a_ddl_postgresql_v1.sql
-- Kyudai Campus SNS v1 — PostgreSQL 16 初期DDL（pg_trgm + 推奨CHECK/部分Index込み）
-- 想定ID形式: prefix_ULID（TEXT） 例: thr_01J...

BEGIN;

-- 拡張
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =========================
-- users / credentials / sessions
-- =========================
CREATE TABLE users (
  id               TEXT PRIMARY KEY,                      -- usr_*
  role             TEXT NOT NULL DEFAULT 'student',
  faculty          TEXT,                                   -- 学部（任意）
  year             SMALLINT,                               -- 学年（任意, 1..10）
  faculty_public   BOOLEAN NOT NULL DEFAULT false,         -- 公開フラグ
  year_public      BOOLEAN NOT NULL DEFAULT false,         -- 公開フラグ
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_users_faculty_len CHECK (faculty IS NULL OR char_length(faculty) BETWEEN 1 AND 50),
  CONSTRAINT ck_users_year_range CHECK (year IS NULL OR (year BETWEEN 1 AND 10))
);

CREATE TABLE credentials (
  id           TEXT PRIMARY KEY,                           -- cre_*
  user_id      TEXT NOT NULL REFERENCES users(id),
  provider     TEXT NOT NULL CHECK (provider IN ('device','email_otp','azure_ad')),
  subject      TEXT NOT NULL,                              -- 外部ID（device/email/aad）
  secret_hash  TEXT,                                       -- 任意
  is_primary   BOOLEAN NOT NULL DEFAULT false,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_used_at TIMESTAMPTZ,
  UNIQUE (provider, subject)
);

CREATE TABLE sessions (
  id          TEXT PRIMARY KEY,                            -- ses_*
  user_id     TEXT NOT NULL REFERENCES users(id),
  token_hash  TEXT NOT NULL UNIQUE,                        -- sha256(token)
  expires_at  TIMESTAMPTZ NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================
-- threads / comments
-- =========================
CREATE TABLE threads (
  id                TEXT PRIMARY KEY,                      -- thr_*
  author_id         TEXT NOT NULL REFERENCES users(id),
  title             TEXT NOT NULL,
  body              TEXT NOT NULL,
  up_count          INTEGER NOT NULL DEFAULT 0,
  save_count        INTEGER NOT NULL DEFAULT 0,
  solved_comment_id TEXT,                                  -- 物理FKなし（アプリで整合）
  heat              INTEGER NOT NULL DEFAULT 0,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_activity_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at        TIMESTAMPTZ
);

CREATE TABLE comments (
  id          TEXT PRIMARY KEY,                            -- cmt_*
  thread_id   TEXT NOT NULL REFERENCES threads(id),
  author_id   TEXT NOT NULL REFERENCES users(id),
  body        TEXT NOT NULL,
  up_count    INTEGER NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at  TIMESTAMPTZ
);

-- =========================
-- attachments（投稿orコメントに1枚）
-- =========================
CREATE TABLE attachments (
  id          TEXT PRIMARY KEY,                            -- att_*
  thread_id   TEXT REFERENCES threads(id),
  comment_id  TEXT REFERENCES comments(id),
  key         TEXT NOT NULL,                               -- S3 object key
  mime        TEXT NOT NULL,
  width       INTEGER NOT NULL,
  height      INTEGER NOT NULL,
  size        INTEGER NOT NULL,                            -- bytes
  sha256      TEXT NOT NULL,                               -- content hash
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK ((thread_id IS NOT NULL) <> (comment_id IS NOT NULL))  -- XOR: どちらか片方のみ
);

-- MIME 二重ロック
ALTER TABLE attachments
  ADD CONSTRAINT ck_attachments_mime
  CHECK (mime IN ('image/webp','image/jpeg','image/png'));

-- =========================
-- tags（固定4キー）
-- =========================
CREATE TABLE tags (
  thread_id  TEXT NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
  key        TEXT NOT NULL CHECK (key IN ('種別','場所','締切','授業コード')),
  value      TEXT NOT NULL,
  PRIMARY KEY (thread_id, key)
);

-- 値の条件付きCHECK
ALTER TABLE tags
  ADD CONSTRAINT ck_tags_kind_value
  CHECK (
    (key <> '種別' OR value IN ('question','notice','recruit','chat')) AND
    (key <> '場所' OR char_length(value) BETWEEN 1 AND 50) AND
    (key <> '授業コード' OR char_length(value) BETWEEN 1 AND 32) AND
    (key <> '締切' OR value ~ '^\d{4}-\d{2}-\d{2}$')
  );

-- =========================
-- reactions（Up/保存の冪等制約）
-- =========================
CREATE TABLE reactions (
  id           TEXT PRIMARY KEY,                           -- rcn_*
  user_id      TEXT NOT NULL REFERENCES users(id),
  target_type  TEXT NOT NULL CHECK (target_type IN ('thread','comment')),
  target_id    TEXT NOT NULL,                              -- 物理FKなし（両対応のため）
  kind         TEXT NOT NULL CHECK (kind IN ('up','save')),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, target_type, target_id, kind)
);

-- =========================
-- インデックス
-- =========================

-- 検索（pg_trgm）
CREATE INDEX idx_threads_title_trgm ON threads USING gin (title gin_trgm_ops);
CREATE INDEX idx_threads_body_trgm  ON threads USING gin (body  gin_trgm_ops);

-- 「未削除のみ」の部分インデックス（一覧/検索の基本条件）
CREATE INDEX idx_threads_alive_created_desc
  ON threads (created_at DESC, id DESC)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_threads_alive_last_activity
  ON threads (last_activity_at)
  WHERE deleted_at IS NULL;

-- コメント時系列のための部分インデックス
CREATE INDEX idx_comments_alive_thread_created
  ON comments (thread_id, created_at ASC, id ASC)
  WHERE deleted_at IS NULL;

-- タグJOIN/フィルタ軽量化
CREATE INDEX idx_tags_key_value ON tags(key, value);

-- 補助
CREATE INDEX idx_threads_last_activity ON threads(last_activity_at);

COMMIT;

-- 備考:
-- - solved_comment_id: 物理FKなし（コメント削除時はアプリ層で NULL に戻す）
-- - reactions.target_id: thread/comment 両対応のため物理FKなし（アプリで存在検証）
-- - 文字数や本文長はAPI層で検証（DTO 04a 準拠）
-- - soft delete: deleted_at IS NULL を基本条件にする（部分Indexが効く）

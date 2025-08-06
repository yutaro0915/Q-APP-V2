03_data_model_erd_v1.md — データモデル / ERD（v1）
対象：FastAPI + PostgreSQL 16
前提：ソフト削除／匿名ユーザー（任意で学部・学年公開）／各投稿と各コメントに画像1枚／Up・保存／pg_trgm 検索／カーソルページング

0. 目的と設計原則
目的：要件を最小コストで満たし、拡張（OTP/AzureAD、CloudFront、PGroonga 等）にも耐えるスキーマを定義。

原則

正規化は最小限、DB制約で足元を固める（UNIQUE/CHECK/部分Index）。

派生値は遅延一致（再集計可能な形に）。

ソフト削除で会話の整合を維持（deleted_at）。

カーソルに優しいキー（ULID系 + 安定ソート列）。

公開プロフィールは“動的評価”（公開フラグに追従、自動スナップショットは持たない）。

1. 識別子・時刻・文字コード
ID 形式：{prefix}_{ULID}（例：thr_01J5Z...）

prefix ∈ {usr, cre, ses, thr, cmt, att, rcn}

ULID（26文字, Base32）で生成順≒時系列 → カーソル安定に寄与

検証：^(usr|cre|ses|thr|cmt|att|rcn)_[0-9A-HJKMNP-TV-Z]{26}$

時刻：timestamptz（UTC保存）。APIもUTC。表示はJST相対に変換。

文字列：UTF-8。本文はプレーン保存。XSS対策は出力サニタイズ。

2. ERD（エンティティと関連）
scss
コピーする
編集する
Users (1) ──< Credentials (N)
Users (1) ──< Sessions   (N)

Users (1) ──< Threads    (N) ──< Comments (N)
Threads (1) ──< Tags     (N)
Threads (1) ──< Attachments (N)
Comments (1) ──< Attachments (N)

Users (1) ──< Reactions  (N)  ──(target: Thread | Comment)
主な制約

credentials(provider, subject) UNIQUE

sessions.token_hash UNIQUE

tags (thread_id, key) PRIMARY KEY（同キー重複禁止）

reactions (user_id, target_type, target_id, kind) UNIQUE（二重up/保存禁止）

attachments: XOR（thread_id または comment_id どちらか一方）、MIME CHECK

threads.solved_comment_id と reactions.target_id は物理FKなし（アプリで整合）

3. テーブル仕様（フィールド定義）
3.1 users
列	型	制約/説明
id	TEXT	PK（usr_*）
role	TEXT	既定 'student'
faculty	TEXT NULL	学部（≤50）
year	SMALLINT NULL	学年（1..10）
faculty_public	BOOLEAN	既定 false
year_public	BOOLEAN	既定 false
created_at	TIMESTAMPTZ	既定 now()

CHECK：char_length(faculty) BETWEEN 1 AND 50（NULL許容）、year BETWEEN 1 AND 10（NULL許容）

3.2 credentials
id(pk), user_id(fk), provider ∈ ('device','email_otp','azure_ad'), subject（外部ID）、secret_hash?, is_primary, created_at, last_used_at

UNIQUE (provider, subject)

3.3 sessions
id(pk), user_id(fk), token_hash UNIQUE, expires_at, created_at

トークンはハッシュで保存（漏洩リスク低減）

3.4 threads
列	型	説明
id	TEXT PK	thr_*
author_id	TEXT FK→users	投稿者
title	TEXT	1..60（APIで検証）
body	TEXT	0..2000
up_count	INT	既定0
save_count	INT	既定0
solved_comment_id	TEXT NULL	物理FKなし
heat	INT	既定0（0..100想定）
created_at	TIMESTAMPTZ	既定 now()
last_activity_at	TIMESTAMPTZ	既定 now()
deleted_at	TIMESTAMPTZ	ソフト削除

不変：編集不可／いつでも削除（ソフト）／削除時は表示を "[削除済み]" に置換。

3.5 comments
id(pk), thread_id(fk), author_id(fk), body（1..1000）, up_count, created_at, deleted_at

並びは時系列 ASC 固定、ネストなし

3.6 attachments
id(pk), thread_id? fk, comment_id? fk, key, mime, width, height, size, sha256, created_at

CHECK：(thread_id IS NOT NULL) <> (comment_id IS NOT NULL)（XOR）

CHECK：mime IN ('image/webp','image/jpeg','image/png')

各投稿/コメント 0/1枚（アプリ側で担保）

3.7 tags（固定4キー）
thread_id(fk ON DELETE CASCADE), key ∈ ('種別','場所','締切','授業コード'), value, PRIMARY KEY(thread_id,key)

条件付きCHECK：

key='種別' → value ∈ ('question','notice','recruit','chat')

key='場所' → 1..50

key='授業コード' → 1..32

key='締切' → 'YYYY-MM-DD'

3.8 reactions
id(pk), user_id(fk), target_type ∈ ('thread','comment'), target_id, kind ∈ ('up','save'), created_at

UNIQUE (user_id, target_type, target_id, kind)（冪等制約）

target_id は物理FKなし（両テーブルを跨るため・アプリで存在検証）

4. ソフト削除の扱い
スレ削除：deleted_at セット、title/body を "[削除済み]"、TL/検索から除外。コメントは残す。

コメント削除：deleted_at セット、body を "[削除済み]"、画像非表示。

解決コメント削除：同一Txで threads.solved_comment_id = NULL。

復元：管理者のみ・本文は復元不可（再入力）。S3 のオブジェクトは物理削除しないが表示は非表示。

5. 画像（S3）方針
クライアントで長辺2048pxに縮小、EXIF除去、WebP優先。

API /uploads/presign で MIME/size 事前検証 → 直PUT → imageKey を作成APIへ。

TL は CSS で 16:9 サムネ、詳細/コメントは等比、タップでフルスクリーン。

6. インデックス戦略
検索（pg_trgm）

threads(title) GIN gin_trgm_ops

threads(body) GIN gin_trgm_ops

未削除のみの部分Index（TL/検索共通条件）

threads(created_at DESC, id DESC) WHERE deleted_at IS NULL

threads(last_activity_at) WHERE deleted_at IS NULL

comments(thread_id, created_at ASC, id ASC) WHERE deleted_at IS NULL

タグJOIN/フィルタ

tags(key, value)（BTree）

タグの全文検索頻度が高まれば、v1.1 で threads.tags_text（連結キャッシュ列 + GIN）を導入。

7. 派生値の扱い（遅延一致）
up_count/save_count（threads/comments）：
INSERT reactions ... ON CONFLICT DO NOTHING → 影響1行の時だけインクリメント。必要なら再集計ジョブで整合回復可能。

heat（0..100）：
一覧返却時に式で算出 or 5分以上経過時のみ遅延更新。

last_activity_at：コメント作成時に now() へ更新。

8. 代表トランザクション
スレ作成：threads INSERT → tags INSERT ≤4 → attachments INSERT(任意)（同一Tx）

コメント作成：comments INSERT → threads.last_activity_at UPDATE（同一Tx）

リアクション：reactions INSERT ... ON CONFLICT DO NOTHING → 影響1行なら up/save インクリメント（同一Tx）

解決設定/解除：同一スレ・未削除を検証 → solved_comment_id SET/NULL（同一Tx）

コメント削除：本体 deleted_at セット → 該当なら solved_comment_id=NULL（同一Tx）

9. カーソルページングのキー
TL sort=new：ORDER BY created_at DESC, id DESC

アンカー：{ createdAt, id }

Index：threads(created_at DESC, id DESC) WHERE deleted_at IS NULL

TL sort=hot：ORDER BY hot_score(snapshotAt) DESC, created_at DESC, id DESC

アンカー：{ score, createdAt, id }

snapshotAt：1ページ目取得時に固定（有効 24h）

コメント：ORDER BY created_at ASC, id ASC

アンカー：{ createdAt, id }

Index：comments(thread_id, created_at ASC, id ASC) WHERE deleted_at IS NULL

10. 検索（pg_trgm）
対象：threads.title, threads.body（GIN + similarity()）

スコア：similarity(title,q) + 0.2*similarity(body,q) + 弱い時間減衰（24h@snapshotAt）

タグ条件：JOIN tags（key='種別'等のフィルタに対応）。

将来：パフォーマンスに応じて tags_text + GIN へ昇格。

11. 公開プロフィールの付与（動的評価）
DTO（ThreadCard/ThreadDetail/Comment）に authorAffiliation?: { faculty?, year? } を任意で付与。

JOIN users して、以下の CASE で抽出：

CASE WHEN u.faculty_public AND u.faculty IS NOT NULL THEN u.faculty END AS author_faculty

CASE WHEN u.year_public AND u.year IS NOT NULL THEN u.year END AS author_year

両方 null なら DTO 側で authorAffiliation = null。

12. データ保持・監査・バックアップ
監査（アプリログ）：user_id, action, target, at, ip, ua を 7日保持。

バックアップ：RDS 日次スナップショット（保持 7–14日）。

画像：S3 バージョニングなし（v1）。違反等は強制非表示で対処。

13. 容量/パフォーマンス見積り（ラフ）
スレ：テキスト ~0.7KB + インデックス ~1.5KB

コメント：テキスト ~0.2KB + インデックス ~0.6KB

画像：S3 管理（DBはメタのみ）

目安：数万スレ/数十万コメント → t4g.small クラスで十分（適切なIndex前提）

14. マイグレーション戦略
初期適用：03a_ddl_postgresql_v1.sql を適用（拡張・テーブル・Index・CHECK まで含む）。

タグ検索が重い場合：threads.tags_text 追加 + トリガで同期 + GIN（v1.1）。

検索強化が必要：PGroonga 導入は別ブランチで計測してから判断。

認証拡張：credentials の provider に追加、sessions は現行のまま運用可。

15. 代表クエリ（抜粋）
15.1 TL（hot, 20件）
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
  AND (:type IS NULL OR EXISTS (
        SELECT 1 FROM tags g
        WHERE g.thread_id=t.id AND g.key='種別' AND g.value=:type
      ))
  AND (
    :anchorScore IS NULL OR
    ( ((t.up_count + 0.5*COALESCE(uc.cnt,0)) *
        EXP(-EXTRACT(EPOCH FROM (:snapshotAt - t.created_at))/43200)) < :anchorScore )
    OR (
      ((t.up_count + 0.5*COALESCE(uc.cnt,0)) *
        EXP(-EXTRACT(EPOCH FROM (:snapshotAt - t.created_at))/43200)) = :anchorScore
      AND (t.created_at, t.id) < (:anchorCreatedAt, :anchorId)
    )
  )
ORDER BY hot DESC, t.created_at DESC, t.id DESC
LIMIT 20;
15.2 TL（new, 20件）
sql
コピーする
編集する
SELECT t.id, t.title, t.body, t.up_count, t.save_count,
       t.created_at, t.last_activity_at,
       CASE WHEN u.faculty_public AND u.faculty IS NOT NULL THEN u.faculty END AS author_faculty,
       CASE WHEN u.year_public AND u.year IS NOT NULL THEN u.year END AS author_year
FROM threads t
JOIN users u ON u.id = t.author_id
WHERE t.deleted_at IS NULL
  AND (:type IS NULL OR EXISTS (
        SELECT 1 FROM tags g
        WHERE g.thread_id=t.id AND g.key='種別' AND g.value=:type
      ))
  AND (:anchorCreatedAt IS NULL OR (t.created_at, t.id) < (:anchorCreatedAt, :anchorId))
ORDER BY t.created_at DESC, t.id DESC
LIMIT 20;
15.3 コメント一覧（ASC, 20件）
sql
コピーする
編集する
SELECT c.id, c.body, c.up_count, c.created_at,
       CASE WHEN u.faculty_public AND u.faculty IS NOT NULL THEN u.faculty END AS author_faculty,
       CASE WHEN u.year_public AND u.year IS NOT NULL THEN u.year END AS author_year
FROM comments c
JOIN users u ON u.id = c.author_id
WHERE c.thread_id = :threadId
  AND c.deleted_at IS NULL
  AND (:anchorCreatedAt IS NULL OR (c.created_at, c.id) > (:anchorCreatedAt, :anchorId))
ORDER BY c.created_at ASC, c.id ASC
LIMIT 20;
15.4 検索（relevance, 20件）
sql
コピーする
編集する
SELECT t.id, t.title, t.body,
  (GREATEST(similarity(t.title, :q), 0.2*similarity(t.body, :q))
   + 0.2*EXP(-EXTRACT(EPOCH FROM (:snapshotAt - t.created_at))/86400)) AS score,
  t.created_at,
  CASE WHEN u.faculty_public AND u.faculty IS NOT NULL THEN u.faculty END AS author_faculty,
  CASE WHEN u.year_public AND u.year IS NOT NULL THEN u.year END AS author_year
FROM threads t
JOIN users u ON u.id = t.author_id
WHERE t.deleted_at IS NULL
  AND (t.title ILIKE '%'||:q||'%' OR t.body ILIKE '%'||:q||'%'
       OR EXISTS (
         SELECT 1 FROM tags g
         WHERE g.thread_id = t.id AND g.value ILIKE '%'||:q||'%'
       ))
  AND (:anchorScore IS NULL OR (score, t.id) < (:anchorScore, :anchorId))
ORDER BY score DESC, t.id DESC
LIMIT 20;
16. トレードオフと留意点
solved_comment_id / reactions.target_id に物理FKなし → アプリで存在整合（ユニテスト必須）。

タグ全文検索は当面 JOIN で対応。負荷増で tags_text + GIN に昇格。

公開プロフィールは動的（過去投稿も最新の公開設定に追従）。スナップショット化が必要なら v2 で author_snapshot 列を追加。


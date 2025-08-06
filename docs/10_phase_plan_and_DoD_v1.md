10_phase_plan_and_DoD_v1.md — フェーズ計画 / 受け入れ条件（v1・Micro-Issue版フリーズ）
目的：1 Issue = 最大1ファイルの最小粒度で、AIエージェントが暴走できない開発運用にする。
参照：02/03/03a/04/04a/04b/05/06/07/08/09/11

0. 運用ルール（共通・改訂）
Micro-Issue 原則：

One-File Rule：1Issueで変更できるのは1ファイルのみ（例外：テスト1ファイル追加は可）。

差分上限：変更行数（add+del）≤ 120。

クロスレイヤ禁止：Repo / Service / Router / UI は別Issueに分離し依存関係で繋ぐ。

命名：P{phase}-{LAYER}-{AREA}-{ACTION}。例：P2-API-Comments-Repo-List.

依存：depends_on を必須。前工程が完了しないと着手不可。

受け入れ：各Issueは 11_issue_template_v1.md に準拠（機械可読メタ＋DoD 必須）。

フェーズDoD/受け入れテストは前版と同じ（必要箇所だけ追補）。

Phase 0 — 環境初期化（セットアップ）
範囲/DoD：前版と同じ。

想定Issue（Micro）
Infra

P0-INFRA-RDS-Init（手順書md追加）

P0-INFRA-S3-Init（バケットCORS/ポリシー設定md）

P0-INFRA-AppRunner-Front（frontサービス作成手順md）

P0-INFRA-AppRunner-API（apiサービス作成手順md）

P0-INFRA-VPC-Connector（VPC接続md）

API 雛形

P0-API-Main-Scaffold（api/app/main.py 新規）

P0-API-Router-Core（api/app/routers/__init__.py）

P0-API-Errors（api/app/core/errors.py）

P0-API-Health（api/app/routers/health.py：/health 200）

Front 雛形

P0-FRONT-NextApp-Init（front/app/layout.tsx）

P0-FRONT-DesignTokens（front/styles/globals.css）

P0-FRONT-APIClient（front/lib/api.ts 基礎）

目安：10–12件

Phase 1 — コア掲示板（スレ作成/閲覧/削除）
DoD/受け入れ：前版 + 下記実装完了。

想定Issue（Micro）
API / Schema & Infra

P1-API-Schemas-ThreadDTO（api/app/schemas/threads.py）

P1-API-DB-Pool（api/app/core/db.py 接続プール）

P1-API-Repo-Threads-Init（api/app/repositories/threads_repo.py 新規）

P1-API-Repo-Threads-Insert

P1-API-Repo-Threads-GetById

P1-API-Repo-Threads-ListNew

P1-API-Repo-Threads-SoftDelete

P1-API-Service-Threads-Create（api/app/services/threads_service.py）

P1-API-Service-Threads-Get

P1-API-Service-Threads-ListNew

P1-API-Service-Threads-Delete

P1-API-Router-Threads-POST（api/app/routers/threads.py）

P1-API-Router-Threads-GET-List

P1-API-Router-Threads-GET-Detail

P1-API-Router-Threads-DELETE

P1-API-Auth-Bootstrap（api/app/routers/auth.py：/auth/bootstrap）

P1-API-Auth-Session（/auth/session GET）

API / Tests

P1-API-Test-Threads-Create（api/tests/test_threads_create.py）

P1-API-Test-Threads-ListNew

P1-API-Test-Threads-Delete

P1-API-Test-Auth

Front

P1-FRONT-Routes-TL-New（front/app/page.tsx SSR）

P1-FRONT-Components-ThreadCard（front/components/ThreadCard.tsx）

P1-FRONT-Routes-ThreadDetail（front/app/thread/[id]/page.tsx）

P1-FRONT-Components-ThreadForm（front/components/ThreadForm.tsx）

P1-FRONT-Actions-CreateThread（front/lib/actions/createThread.ts）

P1-FRONT-Actions-DeleteThread

P1-FRONT-UX-DeleteConfirm（ダイアログ）

目安：30件前後

Phase 2 — コメント/リアクション/解決/プロフィール
想定Issue（Micro）
API / Comments

P2-API-Schemas-Comments（api/app/schemas/comments.py）

P2-API-Repo-Comments-Init（api/app/repositories/comments_repo.py）

P2-API-Repo-Comments-Insert

P2-API-Repo-Comments-ListAsc

P2-API-Repo-Comments-SoftDelete

P2-API-Service-Comments-Create（api/app/services/comments_service.py）

P2-API-Service-Comments-ListAsc

P2-API-Service-Comments-Delete

P2-API-Router-Comments-POST（api/app/routers/comments.py）

P2-API-Router-Comments-GET-List

P2-API-Router-Comments-DELETE

Tests：Create / List / Delete（3件）

API / Reactions

P2-API-Schemas-Reactions（api/app/schemas/reactions.py）

P2-API-Repo-Reactions-Init（api/app/repositories/reactions_repo.py）

P2-API-Repo-Reactions-UpsertUp

P2-API-Repo-Reactions-UpsertSave

P2-API-Service-Reactions-ThreadUp

P2-API-Service-Reactions-ThreadSave

P2-API-Service-Reactions-CommentUp

P2-API-Router-Reactions-Thread

P2-API-Router-Reactions-Comment

Tests：ThreadUp/Save 重複=409、CommentUp 重複=409（2–3件）

API / Solve

P2-API-Service-Solve-Set（api/app/services/solve_service.py）

P2-API-Service-Solve-Clear

P2-API-Router-Solve-POST（api/app/routers/solve.py）

Tests：質問以外=400（NOT_APPLICABLE）、削除時自動解除

API / Profile

P2-API-Repo-Profile（api/app/repositories/profile_repo.py）

P2-API-Service-Profile

P2-API-Router-Profile-GET-PATCH

Tests：公開ON/OFFでDTOが変わる

Front / Comments & Reactions

P2-FRONT-Components-CommentItem（front/components/CommentItem.tsx）

P2-FRONT-Components-CommentForm

P2-FRONT-Actions-CreateComment

P2-FRONT-Actions-DeleteComment

P2-FRONT-Actions-ReactionThread

P2-FRONT-Actions-ReactionComment

P2-FRONT-UX-PinnedSolved（解決コメント固定表示）

Tests(E2E)：ThreadDetailの操作一式（1件）

Front / Profile

P2-FRONT-Routes-Profile（front/app/me/profile/page.tsx）

P2-FRONT-Actions-UpdateProfile

P2-FRONT-UX-AuthorChip（学部/学年バッジ）

目安：40件前後（合計）

Phase 3 — 画像/検索/タグ
想定Issue（Micro）
API / Uploads（S3）

P3-API-Infra-S3Client（api/app/infra/s3.py）

P3-API-Service-Uploads-Presign（api/app/services/uploads_service.py）

P3-API-Router-Uploads-Presign（api/app/routers/uploads.py）

Tests：MIME/size 検証 400、成功 200

API / Attachments

P3-API-Repo-Attachments（api/app/repositories/attachments_repo.py）

P3-API-Service-Attachments-LinkThread

P3-API-Service-Attachments-LinkComment

Tests：HEAD検証・CHECK違反400

API / Search

P3-API-Repo-Search（api/app/repositories/search_repo.py）

P3-API-Service-Search

P3-API-Router-Search-GET

Tests：relevance/new、snapshotカーソル、2ページ重複なし

Front / Uploads

P3-FRONT-Utils-ImagePreprocess（front/lib/image/preprocess.ts：2048/EXIF除去/WebP）

P3-FRONT-Actions-PresignPut（PUT実装）

P3-FRONT-Components-ImageViewer（フルスクリーン）

P3-FRONT-Integrate-ThreadForm-Image

P3-FRONT-Integrate-CommentForm-Image

Front / Search

P3-FRONT-Routes-Search（front/app/search/page.tsx）

P3-FRONT-Components-SearchBox

P3-FRONT-Integrate-SearchList

目安：30件前後

Phase 4 — Hot/熱量/プレビュー
想定Issue（Micro）
API / Hot & Heat

P4-API-Repo-Threads-Uniq3h（ユニーク投稿者集計）

P4-API-Service-Threads-HotScore（式＋遅延更新）

P4-API-Router-Threads-ListHot（sort=hot）

Tests：スコア降順・snapshot固定

Front / TL強化

P4-FRONT-Components-HeatChip

P4-FRONT-Card-LatestReplyPreview（1行プレビュー）

P4-FRONT-Routes-TL-HotTab（タブ切替）

UX Tests：プレビュー省略記号、タブ状態保持

目安：10–12件

総件数目安
P0: ~12

P1: ~30

P2: ~40

P3: ~30

P4: ~12
合計：~124件（テスト含む）

付録A — 依存グラフ指針（抜粋）
Repo → Service → Router → Front Actions → UI の順で直列。

例：P2-API-Repo-Comments-ListAsc → P2-API-Service-Comments-ListAsc → P2-API-Router-Comments-GET-List → P2-FRONT-Integrate-ThreadDetail-Comments.

付録B — 受け入れゲート（再掲）
機能・非機能・運用ゲートは前版と同じ（08/09準拠）。

各Phase終了時にTL/詳細/コメント/検索のE2Eが手動で通ること。

付録C — エージェント実行制約（最小コマンド）
カスタムコマンド（例）。詳細は 11 に従う。

APPLY_PATCH(file, unified_diff)：単一ファイル差分のみ適用

ADD_FILE(file, content)：新規1ファイル追加

RUN_TESTS(scope)：該当階層のみ実行

LINT(scope)：lint

REPORT(status, changes, lines_changed)：実績を出力（120行以下保証）


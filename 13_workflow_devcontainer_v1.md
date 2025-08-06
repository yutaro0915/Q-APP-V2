13_workflow_devcontainer_v1.md — 実運用フロー（シンプル版）
前提

開発は devcontainer（front・api の2コンテナ＋postgresサービス）。

Git/Issue/PR管理はホスト。AIは各コンテナ内で作業。

1 Issue = 1ファイル変更（＋任意でテスト1ファイル）、これだけ守る。行数は気にしない。

0. 最小ルール（これだけ）
One-File Rule：target_file 1つだけ触る（＋任意 test_file 1つ）。

1PR=1Issue、ブランチ名=issue.id。

PR本文の先頭に**IssueのYAMLメタ（11番テンプレ）**を貼る。

並行排他：同じ target_file は同時に配らない（ホスト側でロック）。

1. 1日の流れ（ホスト視点）
ReadyなIssueを選ぶ（depends_on満たすやつだけ）。

ロック作成：.locks/<target_file>.lock を置く。

ブランチ作成：git checkout -b <issue.id>

devcontainer起動（front/api両方）

AIにIssue渡す（YAMLメタをそのまま入力 or ファイル参照）

PRが出たらレビュー（下のチェックリストだけ見る）

OKならマージ（squash）、ロック削除。

次のIssueへ。

2. AI（コンテナ内）の手順（必ずこの順番）
ISSUE_FETCH：YAMLメタを取り込み、target_file と test_file を記憶。

BRANCH：すでにブランチ切れてる前提（なければ作る）。

TDD：

まず テストを書く（test_file だけ追加/修正）→ テストREDを確認。

実装（target_file だけを編集）→ テストGREENにする。

SELF_CHECK（超シンプル）：

変更ファイルが target_file と test_file 以外に無いこと。

もし混ざってたら差分を元に戻す/分割提案。

COMMIT & PUSH：メッセージ "{issue.id}: {短い要約}"。

OPEN_PR：PR本文の先頭にYAMLメタ、続けて簡単な説明。

REPORT：テスト結果/変更ファイル一覧だけを出力。（人間が見る）

使うコマンドはこれだけ：READ/LIST/ADD_FILE/APPLY_PATCH/RUN_TESTS/COMMIT/PUSH/OPEN_PR/REPORT
外部ネットは禁止。DBは devcontainer の postgres を使う（03aのDDL導入済み）。

3. レビューの見方（人間）
PR本文のYAMLメタがあるか（11テンプレ準拠）。

変更ファイルが2つ以内か（target_file と 任意で test_file）。

仕様に沿ってるか（spec_refs で 04/04a/04b/03a を確認）。

テストがGREENか。

APIなら エラー形式(04b) と X-Request-Idログが出てるか（詰めすぎない）。

OKならマージ。ダメなら「対象外ファイル混入」「仕様逸脱」のどちらかだけ指摘して差し戻す。

4. 依存と排他（ホスト側ミニ運用）
配布前に depends_on を見て、未完があれば配らない（BLOCKED扱い）。

排他：同じ target_file を触るIssueは同時配布しない。.locks/で原始的にOK。

分割が必要になったら：AIが分割提案→ホストがIssueを2つに分ける（片方を depends_on に設定）。

5. devcontainerの最低限
api：FastAPI・pytest。起動時にDDL（03a）を流すスクリプトを用意。

front：Next.js・vitest/Playwrightどちらでも。

postgres：16。テスト前にDB初期化（トランザクションロールバック型でもOK）。

コードはホストをbind mount。Gitはホストのみ。

6. 失敗時の対処
対象外ファイルが混ざったPR → 速攻Close、AIに「target_fileだけで再提出」指示。

テストが赤 → 原因要約をもらって1回だけ再トライ。無理なら人間が引き継ぐ。

仕様変更が必要 → Issueをクローズし、仕様ドキュメント側（04/04a など）を先に更新。
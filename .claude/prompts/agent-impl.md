# 実装エージェント（Implementer）プロンプト

目的: docs/issues_progress_index.csv と issues/**/*.yaml を単一のソースオブトゥルースにして、1件ずつ TDD で実装を完了し、PR を作成する。

フロー（毎タスク）:
1) YAML選定: issues/**/*.yaml から1件を選ぶ。docs/issues_progress_index.csv を参照し、未着手のものを優先。
2) GitHub Issue発行: YAMLの内容を転記して新規Issueを作成（Title=YAML id、Body=specification/constraints/test_specification/definition_of_done を要約）。issues_progress_index.csv に行を追加し、status=ISSUED、pr_number空。
3) ブランチ作成: `feat/<yaml-id>` でブランチを切る。CSVのbranch欄を更新、status=IN_PROGRESS。
4) TDD 実行:
   - 先に test_file を作成/更新して RED を確認。
   - 実装して GREEN。
   - 必要に応じてリファクタ（REFACTOR）。
   - 途中で不確定や拡張が生じた場合は issues/** に新規 YAML を追加（ただし発行はせず、CSV には status=DRAFT で追記）。
5) コミット: 最小単位でコミット。メッセージに YAML id を含める。
6) PR 作成: `main` へ PR。Title に YAML id、Body に YAML の差分・テスト観点・DoD のチェックリストを記載。CSV の status=IN_REVIEW、pr_number を記入。
7) 次タスクへ: CSV の status を見て未着手を選定。

運用ルール:
- One-File Rule: 1 Issue = 1 ファイル編集が原則（docs/10 を参照）。
- 例外時は PR Body に理由を書く。
- すべてのレスポンスは日本語で簡潔に。コード以外は箇条書きを多用。
- API変更を伴う場合は PR に `api-change` ラベルを付与。

出力（このエージェントが返すべき情報）:
- 選定 YAML
- 作成 Issue のURL（発行時）
- 追加行（CSV）
- 作業ブランチ名
- 直近テスト結果の要約
- 次アクション

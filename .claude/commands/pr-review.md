# PR Review

Pull Requestのレビューとマージを実行します。

## 実行手順

1. **PR情報取得**
   ```
   gh pr view {pr_number} --json number,title,body,mergeable,state,files,checks
   ```

2. **PR本文のメタデータ確認**
   PR本文の先頭に以下のメタデータが含まれていることを確認:
   ```
   Issue: #{issue_number}
   ID: {issue_id}
   Target: {target_file}
   Test: {test_file}
   ```

3. **変更ファイル数確認**
   - 変更ファイル数が2つ以下であることを確認
   - target_fileとtest_fileのみが変更されていることを確認
   - docs/やissues/の変更は含まない

4. **CI結果確認**
   ```
   gh pr checks {pr_number}
   ```
   以下のチェックがすべてPASSしていることを確認:
   - backend-test（backendの場合）
   - frontend-test（frontendの場合）
   - check-files（2ファイル制限）

5. **マージ実行**
   すべての条件を満たしている場合:
   ```
   gh pr merge {pr_number} --squash --subject "{issue_id}: {要約}"
   ```

6. **Issue更新**
   マージ完了後、関連Issueにコメント追加:
   ```
   gh issue comment {issue_number} --body "PR #{pr_number} merged"
   ```

## 確認項目チェックリスト
- [ ] PR本文にIssueメタデータが存在
- [ ] 変更ファイル数が2以下
- [ ] target_fileとtest_fileのみの変更
- [ ] すべてのCIチェックがPASS
- [ ] コンフリクトなし（mergeable: true）

## エラー時の対処
- **CI失敗**: 失敗内容を確認し、修正を依頼
- **ファイル数超過**: 不要な変更を削除するよう依頼
- **メタデータ不足**: PR本文の修正を依頼
- **コンフリクト**: リベース実行を依頼
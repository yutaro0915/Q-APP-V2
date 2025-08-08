# Progress Update

マージ済みPRの情報を元にCSV進捗を更新します。

## 実行手順

1. **マージ済みPR取得**
   ```
   gh pr list --state merged --json number,mergedAt,title,body --limit 100
   ```

2. **Issue ID抽出**
   各PRから以下の情報を抽出:
   - PR本文のメタデータから`ID: {issue_id}`を取得
   - タイトルから`{issue_id}:`形式を取得
   - Issue番号（`Issue: #{issue_number}`）を取得

3. **CSV読み込み**
   `docs/issues_progress_index.csv`を読み込み:
   ```csv
   id,phase,status,started_at,pr_number,completed_at,blocked_reason
   ```

4. **CSV更新**
   該当するissue_idの行を更新:
   - `status`: pending/in_progress → completed
   - `pr_number`: PR番号を記録（例: #45）
   - `completed_at`: マージ時刻を記録（ISO8601形式）
   - `blocked_reason`: クリア（空文字）

5. **Issue自動クローズ**
   ```
   gh issue close {issue_number} --comment "Completed via PR #{pr_number}"
   ```

6. **依存関係解放**
   完了したIssueに依存していた他のIssueを確認:
   - 該当Issue IDをdepends_onに含むYAMLを検索
   - 依存がすべて解決したIssueをリストアップ
   - 「作業可能になったIssue」として報告

## 更新例

更新前:
```csv
P1-BACKEND-Model-User,1,in_progress,2025-08-07T10:00:00Z,,,
```

更新後:
```csv
P1-BACKEND-Model-User,1,completed,2025-08-07T10:00:00Z,#45,2025-08-07T11:30:00Z,
```

## 注意事項
- 既にcompletedのIssueは更新しない
- PR番号の重複チェック（同じPRで複数Issue更新を防ぐ）
- タイムゾーンはUTC（ISO8601形式）
- CSVのバックアップを作成してから更新
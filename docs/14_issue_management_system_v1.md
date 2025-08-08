# Issue管理システム設計（v1）

## 基本方針

**二層管理システム**:
- **進捗管理層**: CSVによる簡潔な状態追跡（issues_progress_index.csv）
- **定義層**: YAMLによる厳密な仕様定義（issues/phase*/P*.yaml）

## 進捗管理CSV

```csv
id,phase,status,started_at,pr_number,completed_at,blocked_reason
P0-INFRA-RDS-Init,0,pending,,,,
P1-API-Repo-Threads-Insert,1,in_progress,2025-08-07T09:00:00Z,,,
P1-API-Schemas-ThreadDTO,1,completed,2025-08-07T08:00:00Z,#45,2025-08-07T08:30:00Z,
```

**フィールド**:
- id: Issue識別子
- phase: フェーズ番号（0-4）
- status: pending/in_progress/completed/blocked
- started_at: 作業開始時刻
- pr_number: 関連PR番号
- completed_at: 完了時刻
- blocked_reason: ブロック理由

## Issue定義YAML

各Issueの詳細仕様は `issues/phase{0-4}/P*.yaml` に保存。

```yaml
id: P1-API-Repo-Threads-Insert
target_file: api/app/repositories/threads_repo.py
test_file: api/tests/test_threads_repo_insert.py
depends_on: [P1-API-Repo-Threads-Init]
spec_refs: ["03", "05"]
specification:
  # 詳細仕様...
```

## 運用方針

1. YAMLで全Issue定義を作成
2. YAMLからCSV目次を生成
3. CSVで進捗を追跡
4. 詳細が必要な時はYAMLを参照
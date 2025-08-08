---
description: Issue実装（TDDアプローチ）
allowed-tools: [Read, Write, Edit, MultiEdit, Glob, Grep, Bash, LS]
---

# Issue実装

指定されたIssue番号のYAMLを読み込み、TDDアプローチで実装。

1. Issue YAMLを`issues/`から読み込み
2. テストファイル作成/修正（RED確認）
3. target_file実装（GREEN確認）
4. コミット作成: `{issue.id}: {summary}`
5. PR作成（YAML metadata付き）

制約: target_fileとtest_fileのみ修正可能
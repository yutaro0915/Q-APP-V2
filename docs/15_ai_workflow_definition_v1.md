# AI ワークフロー定義（v1）

## ホスト側AI

### 役割
GitHub Issue/PR管理と進捗追跡

### 作業フロー

1. **Issue作成**
   - YAMLファイルから内容を読み込み
   - GitHub Issueとして作成
   - Issue番号を記録

2. **PR確認とマージ**
   - PR本文の先頭にIssueメタデータがあることを確認
   - 変更ファイルが2つ以下であることを確認
   - テストがパスしていることを確認
   - 問題なければsquash merge

3. **CSV更新**
   - マージ完了後、進捗CSVのstatusをcompletedに更新
   - PR番号と完了時刻を記録

## コンテナ側AI

### 役割
Issue実装とPR作成

### 作業フロー

1. **Issue読み込み**
   - 指定されたIssue番号から内容を取得
   - target_file、test_file、仕様を把握
   - spec_refsのドキュメントを参照

2. **TDD実装**
   - test_fileを作成
   - テスト実行してRED確認
   - target_fileを実装
   - テスト実行してGREEN確認

3. **PR作成**
   - git add（target_fileとtest_fileのみ）
   - git commit -m "{issue-id}: {要約}"
   - PR作成、本文先頭にIssueメタデータを含める

4. **自己チェック**
   - 変更ファイルがtarget_fileとtest_fileのみ
   - テストがGREEN
   - 仕様に準拠

## 情報フロー

```
YAML → [ホスト側AI] → GitHub Issue → [コンテナ側AI] → PR → [ホスト側AI] → マージ → CSV更新
```

## 制約

### ホスト側
- 実装内容には関与しない
- 形式的な確認のみ行う

### コンテナ側
- GitHub Issueの内容に従う
- target_file/test_file以外は変更しない
- 外部ネットワークアクセスは最小限（GitHub APIのみ）
# Issue Create

issues/配下のYAMLファイルからGitHub Issueを一括作成します。

## 実行手順

1. **未作成Issueの特定**
   - `docs/issues_progress_index.csv`を読み込み
   - GitHub Issue番号が未記録のIDを抽出
   - 対応するYAMLファイルパスを特定: `issues/phase{N}/{id}.yaml`

2. **YAMLファイル読み込み**
   必須フィールド確認:
   - `id`: Issue識別子（例: P1-BACKEND-Model-User）
   - `phase`: フェーズ番号（0-4）
   - `layer`: BACKEND/FRONTEND/INFRA
   - `area`: Model/Route/Component等
   - `action`: 具体的な動作
   - `target_file`: 実装対象ファイルパス
   - `test_file`: テストファイルパス（nullも可）
   - `depends_on`: 依存Issue IDリスト
   - `spec_refs`: 参照仕様書番号リスト
   - `specification`: 詳細仕様
   - `estimated_loc`: 予想行数

3. **GitHub Issue作成**
   ```
   gh issue create \
     --title "{id}: {specification.purpose}" \
     --body "## 概要\n{specification.purpose}\n\n## 対象ファイル\n- 実装: `{target_file}`\n- テスト: `{test_file}`\n\n## 仕様\n{specification.content_requirements}\n\n## 完了条件\n{definition_of_done}\n\n## 依存関係\n{depends_on}\n\n参照: `issues/phase{phase}/{id}.yaml`" \
     --label "{layer},{area},phase{phase}"
   ```

4. **ラベル作成**
   必要に応じて以下のラベルを自動作成:
   - backend, frontend, infra（layer）
   - model, route, component等（area）  
   - phase0, phase1, phase2, phase3, phase4（phase）

5. **CSV更新**
   作成したIssue番号をCSVに記録:
   - 既存行がある場合: GitHub Issue番号を追記
   - 新規の場合: 新規行として追加
   - フォーマット: `{id},{phase},pending,,,,,`

## 注意事項
- 依存関係（depends_on）が解決していないIssueも作成する
- test_fileがnullの場合は「テストなし」と明記
- spec_refsの番号はdocs/内の対応ドキュメントを指す
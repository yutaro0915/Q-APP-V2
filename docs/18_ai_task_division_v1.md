# ホスト側・コンテナ側AI作業分担（v1）

## ホスト側AI（Git/Issue/PR管理）

### 1. Issue選択と準備
- Ready Issue（依存解決済み）の特定
- ロックファイル作成（.locks/<target_file>.lock）
- ブランチ作成（git checkout -b <issue.id>）
- Issue情報の取得（YAML読み込み）

### 2. 環境管理
- devcontainer起動/停止
- コンテナへのファイル受け渡し
- コンテナ側AIの起動コマンド実行

### 3. PR管理
- PR作成状況の監視
- PR本文のYAMLメタ確認
- レビューチェックリスト実行
  - 変更ファイル数（≤2）
  - YAMLメタの存在
  - 仕様準拠の確認

### 4. マージと後処理
- Squash merge実行
- ロックファイル削除
- CSVステータス更新
- mainブランチへの切り替え

### 5. エラーハンドリング
- 対象外ファイル混入時の差し戻し
- テスト失敗時の再試行判断
- blockedステータスへの変更

## コンテナ側AI（実装作業）

### 1. Issue理解
- YAMLメタの読み込み
- target_file/test_fileの確認
- spec_refsの参照（ドキュメント確認）

### 2. TDD実装
- **Step 1**: テストファイル作成（test_file）
- **Step 2**: テスト実行→RED確認
- **Step 3**: 実装ファイル作成/修正（target_file）
- **Step 4**: テスト実行→GREEN確認

### 3. 自己検証
- 変更ファイルがtarget_file/test_fileのみか確認
- 仕様（spec_refs）との照合
- 変更行数の確認（estimated_loc以下）

### 4. コミット作成
- メッセージ: "{issue.id}: {短い要約}"
- git add（target_file, test_file）
- git commit

### 5. プッシュとPR
- git push origin <issue.id>
- PR作成（YAMLメタを本文先頭に）
- 簡潔な説明追加

## 役割の境界

### ホスト側の責任範囲
- Git操作（ブランチ管理、マージ）
- GitHub連携（Issue、PR）
- 進捗管理（CSV更新）
- 排他制御（ロック）
- 品質ゲート（レビュー）

### コンテナ側の責任範囲
- コード実装
- テスト作成/実行
- 仕様準拠の確認
- コミット作成
- PR起票

### 情報の受け渡し
```
ホスト → コンテナ:
- Issue YAML（.current-issue.yaml）

コンテナ → ホスト:
- PR作成完了の通知（PR番号）
- テスト結果
- 変更ファイルリスト
```

## 制約事項

### ホスト側
- コンテナ内のファイルを直接編集しない
- PR本文のYAMLメタ以外は見ない
- 実装の詳細には介入しない

### コンテナ側
- target_file/test_file以外を変更しない
- 外部ネットワークアクセスなし
- Issue管理/進捗更新はしない

## エラー時の連携

1. **テスト失敗が続く場合**
   - コンテナ側: エラー詳細をレポート
   - ホスト側: blockedに変更、人間に通知

2. **仕様の曖昧さ**
   - コンテナ側: 具体的な質問を出力
   - ホスト側: Issue YAMLに clarification追記

3. **対象外ファイル変更**
   - コンテナ側: 本来は発生しないはず
   - ホスト側: PR却下、やり直し指示
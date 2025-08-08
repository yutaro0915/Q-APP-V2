# AI ワークフロー定義（v1）

## ホスト側AI（main直運用）

### 役割
コミット後の自動検証と進捗追跡（PR/ブランチは使用しない）

### 作業フロー

1. **Issue作成（任意）**
   - YAMLファイルから内容を読み込み
   - 必要であれば GitHub Issue としても作成
   - Issue番号は任意でCSVへ記録可

2. **コミット監視と検証**
   - 直近コミットの変更ファイル数（実装+テスト≤2相当）を確認
   - `scripts/test.sh` を実行し backend/frontend GREEN を確認
   - YAML先頭に占有スタンプがある場合は整合性を目視確認

3. **CSV更新**
   - 実装完了後、進捗CSVの status を completed に更新
   - 完了時刻を記録（pr_number は空で可）

## コンテナ側AI（実装エージェント）

### 役割
Issue実装と main への直接コミット

### 作業フロー

1. **YAML読み込み/占有**
   - 対象の `issues/**.yaml` を開く
   - YAML先頭へ占有スタンプコメントを追加→即コミット/Push
   - target_file、test_file、仕様、spec_refs を把握

2. **TDD実装**
   - test_fileを作成・RED確認
   - target_fileを実装・GREEN確認（`scripts/test.sh`）

3. **コミット**
   - 実装1ファイル＋テストのみを `git add`
   - `git commit -m "{issue-id}: {要約}" && git push origin main`

4. **自己チェック**
   - 実装ファイルは1つ（テスト除く）
   - テストがGREEN
   - 仕様に準拠（YAML/04/04a/04b/03a/05/06）

## 情報フロー（main直）

```
YAML（占有スタンプ） → [コンテナ側AI] 直コミット → 自動テスト → [ホスト側AI] 検証 → CSV更新
```

## 制約

### ホスト側
- 実装内容には関与しない
- 形式的な確認のみ行う

### コンテナ側
- YAML/仕様に従う
- target_file/test_file以外は変更しない
- 外部ネットワークアクセスは最小限
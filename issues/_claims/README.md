# Issues Claim（簡易ロック運用）

複数エージェントの同時開発で競合を避けるための「超軽量ロック」仕組みです。Git上のテキストファイルのみを用います。

## ルール（運用）
1. ある YAML Issue に着手したい場合、まず「Claim 専用PR」を作成し、`issues/_claims/<ISSUE_ID>.claim` を追加します。
   - 例: `issues/_claims/P2-API-Repo-Comments-Insert.claim`
   - 中身は YAML への参照と担当者/開始時刻のみ（テンプレート下記）。
2. Claim 専用PRがマージされたら、実装を開始します。
3. 実装PRでは、着手中の Claim ファイルを必ず削除してください（CIが強制）。
4. 別の人が同じ Issue を Claim 済みの場合は、Claim 専用PRがCIで弾かれてマージできません。

## ファイル形式（テンプレート）
```
issue_id: P2-API-Repo-Comments-Insert
title: P2-API-Repo-Comments-Insert
assignee: your_name_or_bot
start_at: 2025-08-08T00:00:00Z
ref: issues/phase2/P2-API-Repo-Comments-Insert.yaml
notes: ""
```

## メリット
- 追加のインフラ不要（Gitのみ）。
- Claim → 実装 の2段階PRに分けることで、衝突を事前に可視化。
- 実装PRでは Claim の削除チェックを必須化し、ロック解除漏れを防止。

## 注意
- One-File Rule により、実装PRでは基本1ファイル＋テストのみの変更です。Claimの削除が追加で入りますが、CIの変更ファイル数上限ルール（2ファイルまで）に収まるようにしています。
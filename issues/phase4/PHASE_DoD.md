# Phase 4 — Hot/熱量/プレビュー DoD

このフェーズの目的は、Hot（時間減衰付きスコア）による並び替えと、一覧の視認性向上（HeatChip/最新返信プレビュー）を完成させることです。

## 達成状態（ゴール）
- TL ホットタブ: `GET /threads?sort=hot` が動作し、snapshotAt で順序固定、カーソルで安定ページング（24h）。
- Hot 計算式は 03/05 準拠（(up_count + 0.5*uniq3h) * exp(-hours_since_created/12)）。
- フロント: Hot/New 切替、3h参加者バッジ（HeatChip）、1行の最新返信プレビュー表示。

## API 完了条件
- `GET /threads?sort=hot`（公開）→ PaginatedThreadCards
  - 並び: (score DESC, createdAt DESC, id DESC)
  - ヘッダ: `X-Snapshot-At` 付与
- uniq3h 集計: snapshotAt 基準で直近3hの `comments.author_id` の DISTINCT 数

## DB/Repo 仕様（抜粋）
- `comments` の部分Index（ASC）を活用。集計クエリは snapshotAt を引数に持つ。

## サービス/ルーター
- Hot: クエリ時算出 or 5分以上経過時のみ遅延更新（任意運用）。
- カーソル: anchor(score, createdAt, id) でタプル比較、24h で期限切れ。

## フロント
- Hot/New タブ切替（URLパラメータ）。
- HeatChip（🔥 + 3h参加者数）をThreadCardに併記。
- 最新返信プレビュー（削除済みは "[削除済み]"）。

## 受け入れテスト（例）
- sort=hot/new の2ページ目が重複しない。
- snapshotAt がヘッダに返り、24h超過で 400。
- プレビューは1行省略、HeatChipのレベル表示が想定と一致。

## 参照
- 04/04a/04b/03/03a/05/06（各該当章）
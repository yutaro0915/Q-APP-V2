# AWS デプロイ・ロードマップ（動的更新）

最終更新: (初期作成)

## 目標
- Front/API を AWS App Runner で本番稼働
- RDS(PostgreSQL16) を私設接続（VPC Connector）
- 画像 S3（public-read + presign PUT）
- 監視/ログ: CloudWatch Logs、RDS スナップショット

## マイルストーン
- M1: CI 安定化 / Phase1 GO（完了）
- M2: App Runner dev 環境（front/api）立上げ
- M3: RDS dev 接続（VPC Connector）
- M4: S3 バケット/権限確立（presign）
- M5: ドメイン/TLS 構成（Front/API）
- M6: stg/prod 切替手順とロールバック

## 作業項目（抜粋）
- App Runner x2（front/api）
- VPC Connector（RDS 私設アクセス）
- RDS 初期化/接続（03a DDL）
- S3（バケット/ポリシー/ライフサイクル）
- CI/CD（main push→deploy、手動承認）
- 環境変数・シークレットの整備

## リスク
- コスト / スループット / 接続プール上限
- VPC egressの疎通 / セキュリティグループ
- スキーマ移行（将来）

## 依存
- Phase到達（Phase1=GO済、Phase2〜継続）
- CI がGREEN
- E2Eの主要フロー

## 直近の次アクション
- dev環境のApp Runner 雛形に変数差し込み（deploy/apprunner/*.yaml）
- RDS接続のための VPC Connector の具体値（ARN等）収集

# AWS App Runner APIサービスセットアップ手順書

## 1. 前提条件
- AWSアカウントへのアクセス権限
- ECRリポジトリが作成済み
- RDSインスタンスが起動済み（P0-INFRA-RDS-Init完了）
- VPC Connectorが設定済み（P0-INFRA-VPC-Connector完了）

## 2. App Runnerサービス作成

### 2.1 基本設定
1. AWSコンソールでApp Runnerサービスページへ移動
2. 「サービスを作成」をクリック
3. 以下の設定を入力：

| 項目 | 設定値 |
|------|--------|
| サービス名 | kyudai-api |
| ソースタイプ | コンテナレジストリ |
| プロバイダー | Amazon ECR |
| ECRイメージURI | `[AWSアカウントID].dkr.ecr.ap-northeast-1.amazonaws.com/kyudai-api:latest` |

### 2.2 サービス設定

#### リソース設定
| 項目 | 設定値 |
|------|--------|
| CPU | 0.25 vCPU |
| メモリ | 0.5 GB |
| ポート | 8080 |

#### ヘルスチェック設定
| 項目 | 設定値 |
|------|--------|
| プロトコル | HTTP |
| パス | /api/v1/health |
| 間隔 | 20秒 |
| タイムアウト | 5秒 |
| 失敗しきい値 | 3回 |
| 成功しきい値 | 1回 |

## 3. 環境変数設定

App Runnerサービスの環境変数セクションで以下を設定：

```bash
# データベース接続
DATABASE_URL=postgresql://kyudai_user:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/kyudai_sns

# CORS設定（フロントエンドURL）
CORS_ORIGINS=https://kyudai-front.awsapprunner.com,http://localhost:3000

# 環境設定
ENV=production

# ログレベル
LOG_LEVEL=info

# セッション設定
SESSION_TTL_SECONDS=604800

# レート制限設定
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
```

### 環境変数の管理（推奨）
セキュリティのため、以下の機密情報はAWS Systems Manager Parameter Storeまたは Secrets Managerで管理：

- `DB_PASSWORD`: RDSパスワード
- `RDS_ENDPOINT`: RDSエンドポイント

## 4. VPC Connector設定

### 4.1 VPC Connector作成（未作成の場合）
1. App Runnerサービス設定の「ネットワーキング」タブへ移動
2. 「VPC connector」セクションで「新規追加」を選択
3. 以下を設定：

| 項目 | 設定値 |
|------|--------|
| コネクター名 | kyudai-vpc-connector |
| VPC | RDSが配置されているVPC |
| サブネット | プライベートサブネット（2つ以上選択） |
| セキュリティグループ | sg-apprunner |

### 4.2 セキュリティグループ設定（sg-apprunner）

インバウンドルール：なし（App Runnerからの接続のみ）

アウトバウンドルール：
| タイプ | プロトコル | ポート | 送信先 |
|--------|-----------|--------|--------|
| PostgreSQL | TCP | 5432 | RDSセキュリティグループ |
| HTTPS | TCP | 443 | 0.0.0.0/0 |

## 5. 自動デプロイ設定

### 5.1 ECRプッシュトリガー設定
1. App Runnerサービス設定の「ソースとデプロイ」タブへ移動
2. 「自動デプロイ」を有効化
3. 以下を設定：

| 項目 | 設定値 |
|------|--------|
| デプロイトリガー | ECRイメージプッシュ時 |
| イメージタグ | latest |

### 5.2 デプロイ設定
| 項目 | 設定値 |
|------|--------|
| デプロイ戦略 | ローリングデプロイ |
| 最大同時実行数 | 1 |
| ヘルスチェック待機時間 | 60秒 |

## 6. デプロイ確認方法

### 6.1 サービス起動確認
```bash
# ヘルスチェックエンドポイントの確認
curl https://[サービスURL]/api/v1/health

# 期待されるレスポンス
{"status":"healthy"}
```

### 6.2 ログ確認
1. CloudWatchコンソールへ移動
2. ロググループ `/aws/apprunner/kyudai-api/[サービスID]/application` を確認
3. 起動ログとエラーログを確認

### 6.3 メトリクス確認
App Runnerコンソールの「メトリクス」タブで以下を確認：
- リクエスト数
- レスポンス時間
- HTTP 4xx/5xxエラー率
- CPU/メモリ使用率

## 7. トラブルシューティング

### よくある問題と解決方法

#### RDS接続エラー
- VPC Connectorが正しく設定されているか確認
- セキュリティグループのルールを確認
- DATABASE_URL環境変数の形式を確認

#### ヘルスチェック失敗
- アプリケーションログを確認
- ポート番号（8080）が正しいか確認
- `/api/v1/health`エンドポイントが実装されているか確認

#### デプロイ失敗
- ECRイメージが存在するか確認
- IAMロールの権限を確認
- CloudWatchログでエラー詳細を確認

## 8. 運用チェックリスト

### 初回デプロイ時
- [ ] ECRイメージがプッシュされている
- [ ] 環境変数が正しく設定されている
- [ ] VPC Connectorが作成されている
- [ ] ヘルスチェックが成功している
- [ ] RDSへの接続が確立できている

### 継続的デプロイ時
- [ ] 自動デプロイが有効になっている
- [ ] CloudWatchアラームが設定されている
- [ ] バックアップ戦略が確立されている
- [ ] ロールバック手順が明確になっている
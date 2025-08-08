# AWS App Runner VPC Connectorセットアップ手順書

## 1. 概要とアーキテクチャ

### 1.1 VPC Connectorの役割
App Runner VPC Connectorは、App Runnerサービスからプライベートリソース（RDS、ElastiCache等）への接続を可能にします。

### 1.2 ネットワーク構成図（テキスト）
```
Internet
    |
    v
[App Runner Service]
    |
    | (VPC Connector)
    v
[Private Subnet] --- [RDS Instance]
    |
[Security Group: sg-apprunner] ---> [Security Group: sg-rds]
```

## 2. 前提条件
- VPCが作成済み
- プライベートサブネットが2つ以上存在
- RDSインスタンスが作成済み（P0-INFRA-RDS-Init完了）
- App Runnerサービスが作成済み

## 3. セキュリティグループ作成

### 3.1 sg-apprunner作成

#### コンソールから作成
1. EC2コンソールの「セキュリティグループ」へ移動
2. 「セキュリティグループを作成」をクリック
3. 以下の設定を入力：

| 項目 | 設定値 |
|------|--------|
| セキュリティグループ名 | sg-apprunner |
| 説明 | Security group for App Runner VPC Connector |
| VPC | RDSと同じVPCを選択 |

#### インバウンドルール
なし（App Runnerからの通信は自動的に許可）

#### アウトバウンドルール
| タイプ | プロトコル | ポート | 送信先 | 説明 |
|--------|-----------|--------|--------|------|
| PostgreSQL | TCP | 5432 | sg-rds | RDS接続用 |
| HTTPS | TCP | 443 | 0.0.0.0/0 | 外部API通信用 |
| DNS | UDP | 53 | 0.0.0.0/0 | DNS解決用 |

#### CLIから作成
```bash
# セキュリティグループ作成
aws ec2 create-security-group \
  --group-name sg-apprunner \
  --description "Security group for App Runner VPC Connector" \
  --vpc-id [VPC_ID]

# アウトバウンドルール追加（RDS接続）
aws ec2 authorize-security-group-egress \
  --group-id [sg-apprunner-id] \
  --protocol tcp \
  --port 5432 \
  --source-group [sg-rds-id]

# アウトバウンドルール追加（HTTPS）
aws ec2 authorize-security-group-egress \
  --group-id [sg-apprunner-id] \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# アウトバウンドルール追加（DNS）
aws ec2 authorize-security-group-egress \
  --group-id [sg-apprunner-id] \
  --protocol udp \
  --port 53 \
  --cidr 0.0.0.0/0
```

### 3.2 sg-rdsの更新
RDSセキュリティグループにsg-apprunnerからの接続を許可：

```bash
# インバウンドルール追加
aws ec2 authorize-security-group-ingress \
  --group-id [sg-rds-id] \
  --protocol tcp \
  --port 5432 \
  --source-group [sg-apprunner-id]
```

## 4. VPC Connector作成

### 4.1 コンソールから作成
1. App Runnerコンソールへ移動
2. 左側メニューの「VPC connectors」を選択
3. 「VPC connectorを作成」をクリック
4. 以下の設定を入力：

#### 基本設定
| 項目 | 設定値 |
|------|--------|
| VPC connector名 | campus-sns-vpc-connector |
| VPC | RDSが配置されているVPCを選択 |

#### サブネット設定
- プライベートサブネットを2つ以上選択（異なるAZ推奨）
- RDSと同じサブネットグループのサブネットを選択

#### セキュリティグループ
- sg-apprunnerを選択

### 4.2 CLIから作成
```bash
aws apprunner create-vpc-connector \
  --vpc-connector-name "campus-sns-vpc-connector" \
  --subnets "[\"subnet-xxxxx\",\"subnet-yyyyy\"]" \
  --security-groups "[\"sg-apprunner-id\"]" \
  --region ap-northeast-1
```

## 5. App RunnerサービスへのVPC Connector適用

### 5.1 APIサービスへの適用

#### コンソールから
1. App Runnerコンソールで「kyudai-api」サービスを選択
2. 「設定」タブへ移動
3. 「ネットワーキング」セクションで「編集」をクリック
4. VPC Connectorセクションで以下を設定：

| 項目 | 設定値 |
|------|--------|
| VPC connector | campus-sns-vpc-connector |
| VPC connector作成 | 既存のVPC connectorを使用 |

5. 「保存して再デプロイ」をクリック

#### CLIから
```bash
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:ap-northeast-1:[AccountID]:service/kyudai-api/[ServiceID]" \
  --network-configuration '{
    "EgressConfiguration": {
      "EgressType": "VPC",
      "VpcConnectorArn": "arn:aws:apprunner:ap-northeast-1:[AccountID]:vpcconnector/campus-sns-vpc-connector/[ConnectorID]"
    }
  }'
```

### 5.2 サービス再起動
VPC Connector適用後、サービスが自動的に再デプロイされます。
完了まで5-10分程度かかります。

## 6. 接続確認

### 6.1 ヘルスチェック確認
```bash
# APIサービスのヘルスチェック
curl https://[App Runner Service URL]/api/v1/health

# 期待されるレスポンス
{"status":"healthy"}
```

### 6.2 データベース接続確認
アプリケーションログでRDS接続を確認：

1. CloudWatchコンソールへ移動
2. ロググループ `/aws/apprunner/kyudai-api/[ServiceID]/application` を確認
3. 以下のようなログがあることを確認：
   - "Successfully connected to database"
   - エラーログがないこと

### 6.3 テスト用エンドポイント作成（オプション）
```python
# backend/app/routers/health.py に追加
@router.get("/db-health")
async def db_health():
    try:
        # データベース接続テスト
        async with get_db_connection() as conn:
            result = await conn.fetchval("SELECT 1")
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## 7. トラブルシューティング

### VPC Connector作成エラー
#### 症状
VPC Connectorの作成が失敗する

#### 確認項目
1. サブネットが2つ以上選択されているか
2. サブネットが異なるAZに配置されているか
3. IAMロールに必要な権限があるか

#### 解決方法
```bash
# サブネット確認
aws ec2 describe-subnets \
  --subnet-ids subnet-xxxxx subnet-yyyyy \
  --query 'Subnets[*].[SubnetId,AvailabilityZone,VpcId]'
```

### RDS接続エラー
#### 症状
App RunnerサービスからRDSに接続できない

#### 確認項目
1. セキュリティグループルールが正しく設定されているか
2. VPC Connectorが正しくアタッチされているか
3. DATABASE_URL環境変数が正しいか

#### 診断コマンド
```bash
# セキュリティグループルール確認
aws ec2 describe-security-groups \
  --group-ids [sg-apprunner-id] [sg-rds-id] \
  --query 'SecurityGroups[*].[GroupId,IpPermissions,IpPermissionsEgress]'

# VPC Connector状態確認
aws apprunner describe-vpc-connector \
  --vpc-connector-arn "arn:aws:apprunner:ap-northeast-1:[AccountID]:vpcconnector/campus-sns-vpc-connector/[ConnectorID]"
```

### パフォーマンス問題
#### 症状
RDS接続が遅い、タイムアウトする

#### 確認項目
1. VPC Connectorのサブネットとリージョン
2. RDSインスタンスの配置
3. DNS解決の遅延

#### 最適化
- RDSと同じAZのサブネットを優先
- 接続プーリングの実装
- DNS キャッシュの設定

## 8. ベストプラクティス

### 8.1 高可用性
- VPC Connectorに複数のサブネット（異なるAZ）を設定
- セキュリティグループルールは最小限に
- 定期的な接続テストの実装

### 8.2 セキュリティ
- 不要なアウトバウンドルールは削除
- セキュリティグループにタグ付けして管理
- CloudTrailでVPC Connector変更を監査

### 8.3 コスト最適化
- VPC Connectorは複数のApp Runnerサービスで共有可能
- 不要になったVPC Connectorは削除

## 9. 運用チェックリスト

### 初期設定時
- [ ] セキュリティグループ（sg-apprunner）が作成されている
- [ ] VPC Connectorが作成されている
- [ ] App RunnerサービスにVPC Connectorが適用されている
- [ ] RDS接続が確認できている
- [ ] CloudWatchログでエラーがないことを確認

### 定期確認項目
- [ ] VPC Connector の状態が ACTIVE
- [ ] セキュリティグループルールの見直し
- [ ] 接続テストの実行
- [ ] パフォーマンスメトリクスの確認

### 変更時の注意点
- [ ] VPC Connector変更時はサービス再起動が必要
- [ ] セキュリティグループ変更は即座に反映
- [ ] サブネット変更時は新規VPC Connector作成を推奨

## 10. 関連ドキュメント参照先
- [AWS App Runner VPC Connector公式ドキュメント](https://docs.aws.amazon.com/apprunner/latest/dg/network-vpc.html)
- [VPCセキュリティグループベストプラクティス](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
- RDS接続設定: `docs/setup/rds_setup.md`
- App Runner API設定: `docs/setup/apprunner_api_setup.md`
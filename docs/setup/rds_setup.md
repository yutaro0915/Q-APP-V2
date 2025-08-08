# Amazon RDS for PostgreSQL 16 セットアップ手順書

## 1. 前提条件
- AWSアカウントへのアクセス権限
- VPCとサブネットが作成済み
- AWS CLIがインストール済み（DDL適用用）
- psqlクライアントがインストール済み

## 2. RDSインスタンス作成

### 2.1 基本設定
1. AWS RDSコンソールへ移動
2. 「データベースの作成」をクリック
3. 以下の設定を適用：

#### エンジンオプション
| 項目 | 設定値 |
|------|--------|
| エンジンタイプ | PostgreSQL |
| エンジンバージョン | 16.2（最新の16系） |
| テンプレート | 開発/テスト |

#### 設定
| 項目 | 設定値 |
|------|--------|
| DBインスタンス識別子 | kyudai-sns-db |
| マスターユーザー名 | postgres |
| マスターパスワード | 安全なパスワードを生成（Secrets Manager推奨） |

#### インスタンス設定
| 項目 | 設定値 |
|------|--------|
| DBインスタンスクラス | db.t4g.small（開発環境） |
| ストレージタイプ | 汎用SSD (gp3) |
| 割り当てストレージ | 20 GiB |
| ストレージ自動スケーリング | 有効（最大100 GiB） |

### 2.2 接続設定

#### VPC設定
| 項目 | 設定値 |
|------|--------|
| Virtual Private Cloud (VPC) | デフォルトVPCまたは作成済みVPC |
| DBサブネットグループ | 新規作成または既存のプライベートサブネットグループ |
| パブリックアクセス | なし |
| VPCセキュリティグループ | 新規作成（sg-rds） |
| アベイラビリティーゾーン | 指定なし |

#### データベース認証
| 項目 | 設定値 |
|------|--------|
| データベース認証オプション | パスワード認証 |

### 2.3 追加設定

#### データベースオプション
| 項目 | 設定値 |
|------|--------|
| 初期データベース名 | kyudai_sns |
| DBパラメータグループ | default.postgres16 |
| オプショングループ | default:postgres-16 |

#### バックアップ
| 項目 | 設定値 |
|------|--------|
| 自動バックアップ | 有効 |
| バックアップ保持期間 | 7日 |
| バックアップウィンドウ | 03:00-04:00 JST（18:00-19:00 UTC） |

#### モニタリング
| 項目 | 設定値 |
|------|--------|
| 拡張モニタリング | 有効（60秒間隔） |
| Performance Insights | 有効（7日間保持） |

#### メンテナンス
| 項目 | 設定値 |
|------|--------|
| マイナーバージョン自動アップグレード | 有効 |
| メンテナンスウィンドウ | 日曜日 04:00-05:00 JST |

## 3. セキュリティグループ設定

### 3.1 sg-rds セキュリティグループ作成
```bash
# セキュリティグループ作成
aws ec2 create-security-group \
  --group-name sg-rds \
  --description "Security group for RDS PostgreSQL" \
  --vpc-id [VPC_ID]

# インバウンドルール追加（App Runnerからのみ）
aws ec2 authorize-security-group-ingress \
  --group-id [sg-rds-id] \
  --protocol tcp \
  --port 5432 \
  --source-group [sg-apprunner-id]
```

### 3.2 セキュリティグループルール詳細
#### インバウンドルール
| タイプ | プロトコル | ポート | ソース |
|--------|-----------|--------|--------|
| PostgreSQL | TCP | 5432 | sg-apprunner |

#### アウトバウンドルール
なし（デフォルトですべて拒否）

## 4. 拡張機能とDDL適用

### 4.1 接続情報の確認
```bash
# RDSエンドポイント確認
aws rds describe-db-instances \
  --db-instance-identifier kyudai-sns-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

### 4.2 データベース接続と拡張機能有効化
```bash
# データベース接続
export PGPASSWORD='[マスターパスワード]'
psql -h [RDSエンドポイント] -U postgres -d kyudai_sns

# pg_trgm拡張の有効化（検索機能用）
CREATE EXTENSION IF NOT EXISTS pg_trgm;

# UUID生成用拡張（オプション）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# 確認
\dx
```

### 4.3 DDL適用
```bash
# DDLファイルの適用
psql -h [RDSエンドポイント] -U postgres -d kyudai_sns \
  -f docs/03a_ddl_postgresql_v1.sql

# テーブル作成確認
psql -h [RDSエンドポイント] -U postgres -d kyudai_sns -c "\dt"
```

### 4.4 アプリケーション用ユーザー作成（推奨）
```sql
-- アプリケーション用ユーザー作成
CREATE USER kyudai_user WITH PASSWORD '[安全なパスワード]';

-- 権限付与
GRANT CONNECT ON DATABASE kyudai_sns TO kyudai_user;
GRANT USAGE ON SCHEMA public TO kyudai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kyudai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kyudai_user;

-- デフォルト権限設定（今後作成されるオブジェクト用）
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
  GRANT ALL PRIVILEGES ON TABLES TO kyudai_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
  GRANT ALL PRIVILEGES ON SEQUENCES TO kyudai_user;
```

## 5. 環境変数設定

### 5.1 DATABASE_URL形式
```bash
# 基本形式
DATABASE_URL=postgresql://[ユーザー名]:[パスワード]@[エンドポイント]:5432/[データベース名]

# 例（マスターユーザー使用時）
DATABASE_URL=postgresql://postgres:MySecurePass123@kyudai-sns-db.xxxx.ap-northeast-1.rds.amazonaws.com:5432/kyudai_sns

# 例（アプリケーションユーザー使用時）
DATABASE_URL=postgresql://kyudai_user:AppUserPass456@kyudai-sns-db.xxxx.ap-northeast-1.rds.amazonaws.com:5432/kyudai_sns

# SSLを強制する場合
DATABASE_URL=postgresql://kyudai_user:AppUserPass456@kyudai-sns-db.xxxx.ap-northeast-1.rds.amazonaws.com:5432/kyudai_sns?sslmode=require
```

### 5.2 App Runnerでの設定
App Runnerサービスの環境変数に上記のDATABASE_URLを設定

## 6. 接続確認

### 6.1 コマンドラインから
```bash
# 接続テスト
psql "$DATABASE_URL" -c "SELECT version();"

# テーブル一覧確認
psql "$DATABASE_URL" -c "\dt"

# pg_trgm拡張確認
psql "$DATABASE_URL" -c "SELECT * FROM pg_extension WHERE extname = 'pg_trgm';"
```

### 6.2 Pythonから（FastAPI用）
```python
import asyncpg
import os

async def test_connection():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    version = await conn.fetchval('SELECT version()')
    print(f"Connected to: {version}")
    await conn.close()

# 実行
import asyncio
asyncio.run(test_connection())
```

## 7. 運用設定

### 7.1 パフォーマンスチューニング
```sql
-- 接続数設定（パラメータグループで設定）
-- max_connections = 100

-- 共有バッファ（インスタンスメモリの25%）
-- shared_buffers = 256MB

-- work_mem（ソート/ハッシュ用）
-- work_mem = 4MB
```

### 7.2 モニタリング設定
CloudWatchアラーム設定推奨項目：
- CPU使用率 > 80%
- ストレージ空き容量 < 10%
- 接続数 > 80
- レプリケーションラグ > 30秒（読み取りレプリカ使用時）

## 8. トラブルシューティング

### 接続できない
1. セキュリティグループのインバウンドルールを確認
2. VPC/サブネットの設定を確認
3. RDSインスタンスのステータスが「利用可能」か確認
4. エンドポイントのDNS解決を確認

### パフォーマンスが遅い
1. Performance Insightsでクエリ分析
2. インデックスの確認（`EXPLAIN ANALYZE`使用）
3. 接続プーリングの実装検討
4. インスタンスクラスのアップグレード検討

### ストレージ不足
1. 自動スケーリングが有効か確認
2. 不要なログやテンポラリデータの削除
3. VACUUM FULLの実行（メンテナンスウィンドウ内）

### バックアップからの復元
```bash
# スナップショットから復元
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier kyudai-sns-db-restored \
  --db-snapshot-identifier [スナップショットID]

# ポイントインタイムリカバリ
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier kyudai-sns-db \
  --target-db-instance-identifier kyudai-sns-db-pitr \
  --restore-time 2024-01-20T03:30:00.000Z
```

## 9. セキュリティベストプラクティス

1. **マスターパスワードの管理**
   - AWS Secrets Managerで管理
   - 定期的なローテーション

2. **暗号化**
   - 保存時の暗号化を有効化
   - 転送時はSSL/TLS使用

3. **監査ログ**
   - pgauditエクステンションの有効化検討
   - CloudWatch Logsへの出力

4. **最小権限の原則**
   - アプリケーション用ユーザーは必要最小限の権限のみ
   - 読み取り専用ユーザーの作成

## 10. コスト最適化

1. **インスタンスクラス**
   - 開発: db.t4g.micro
   - ステージング: db.t4g.small
   - 本番: db.t4g.medium以上

2. **ストレージ**
   - gp3を使用（gp2より20%安価）
   - 不要なスナップショットの定期削除

3. **リザーブドインスタンス**
   - 本番環境では1年または3年契約で最大72%削減
# AWS App Runner Frontendサービスセットアップ手順書

## 1. 前提条件
- AWSアカウントへのアクセス権限
- AWS CLIがインストール済み
- Dockerがインストール済み
- Next.jsアプリケーションのソースコード

## 2. ECRリポジトリ作成

### 2.1 コンソールから作成
1. Amazon ECRコンソールへ移動
2. 「リポジトリを作成」をクリック
3. 以下の設定を入力：

| 項目 | 設定値 |
|------|--------|
| リポジトリ名 | kyudai-front |
| タグのイミュータビリティ | 無効 |
| スキャン設定 | スキャンオンプッシュ: 有効 |
| 暗号化設定 | AES-256 |

### 2.2 CLIから作成（代替手段）
```bash
aws ecr create-repository \
  --repository-name kyudai-front \
  --image-scanning-configuration scanOnPush=true \
  --region ap-northeast-1
```

## 3. Dockerイメージのビルドとプッシュ

### 3.1 Dockerfile作成
`frontend/Dockerfile`として以下を保存：

```dockerfile
# 依存関係のインストール
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package*.json ./
RUN npm ci

# ビルドステージ
FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 環境変数設定（ビルド時）
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

RUN npm run build

# 本番実行ステージ
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

# セキュリティのためnon-rootユーザー作成
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# ビルド成果物のコピー
COPY --from=build /app/public ./public
COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
```

### 3.2 イメージのビルドとプッシュ
```bash
# ECRログイン
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin \
  [AWSアカウントID].dkr.ecr.ap-northeast-1.amazonaws.com

# イメージビルド
cd frontend
docker build -t kyudai-front:latest .

# タグ付け
docker tag kyudai-front:latest \
  [AWSアカウントID].dkr.ecr.ap-northeast-1.amazonaws.com/kyudai-front:latest

# プッシュ
docker push \
  [AWSアカウントID].dkr.ecr.ap-northeast-1.amazonaws.com/kyudai-front:latest
```

## 4. App Runnerサービス設定

### 4.1 サービス作成
1. AWS App Runnerコンソールへ移動
2. 「サービスを作成」をクリック
3. 以下の設定を適用：

#### ソース設定
| 項目 | 設定値 |
|------|--------|
| サービス名 | kyudai-front |
| ソースタイプ | コンテナレジストリ |
| プロバイダー | Amazon ECR |
| ECRイメージURI | `[AWSアカウントID].dkr.ecr.ap-northeast-1.amazonaws.com/kyudai-front:latest` |

#### サービス設定
| 項目 | 設定値 |
|------|--------|
| CPU | 0.5 vCPU |
| メモリ | 1 GB |
| ポート | 3000 |
| 環境変数 | 以下参照 |

### 4.2 環境変数設定

```bash
# API設定
NEXT_PUBLIC_API_BASE=/api/v1
NEXT_PUBLIC_API_URL=https://kyudai-api.awsapprunner.com

# アプリケーション設定
NEXT_PUBLIC_APP_NAME=Kyudai Campus SNS
NEXT_PUBLIC_APP_ENV=production

# 機能フラグ（オプション）
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_DEBUG=false
```

### 4.3 オートスケーリング設定

| 項目 | 設定値 |
|------|--------|
| 最小インスタンス数 | 1 |
| 最大インスタンス数 | 3 |
| 同時リクエスト数 | 100 |

## 5. ヘルスチェック設定

| 項目 | 設定値 |
|------|--------|
| プロトコル | HTTP |
| パス | / |
| 間隔 | 10秒 |
| タイムアウト | 5秒 |
| 成功しきい値 | 1回 |
| 失敗しきい値 | 3回 |

## 6. カスタムドメイン設定

### 6.1 ACM証明書の作成
1. AWS Certificate Managerコンソールへ移動
2. 「証明書をリクエスト」をクリック
3. パブリック証明書を選択
4. ドメイン名を入力（例：`kyudai-sns.example.com`）
5. DNS検証を選択
6. 検証用CNAMEレコードをDNSに追加

### 6.2 App Runnerでのドメイン関連付け
1. App Runnerサービスの「カスタムドメイン」タブへ移動
2. 「ドメインを関連付ける」をクリック
3. ドメイン名と証明書を選択
4. 提供されたCNAMEレコードをDNSに追加

### 6.3 DNS設定例（Route 53）
```
タイプ: CNAME
名前: kyudai-sns
値: [App Runner提供のドメイン].awsapprunner.com
TTL: 300
```

## 7. デプロイ確認

### 7.1 サービス起動確認
```bash
# サービスURLの確認
curl https://[サービスURL].awsapprunner.com

# カスタムドメイン（設定済みの場合）
curl https://kyudai-sns.example.com
```

### 7.2 ログ確認
CloudWatchロググループ：
- `/aws/apprunner/kyudai-front/[サービスID]/application`

### 7.3 メトリクス監視
App Runnerコンソールの「メトリクス」タブで確認：
- リクエスト数
- レスポンス時間（P50, P99）
- 4xx/5xxエラー率
- アクティブインスタンス数

## 8. CI/CDパイプライン設定

### 8.1 GitHub Actionsワークフロー例
```yaml
name: Deploy to App Runner

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1
      
      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: kyudai-front
          IMAGE_TAG: ${{ github.sha }}
        run: |
          cd frontend
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
                     $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
```

## 9. トラブルシューティング

### イメージプルエラー
- ECRリポジトリのアクセス権限を確認
- App RunnerサービスロールにECR読み取り権限があるか確認

### ビルドエラー
- `next.config.js`で `output: 'standalone'` が設定されているか確認
- Node.jsバージョンの互換性を確認（v20推奨）

### 503 Service Unavailable
- ヘルスチェックのパスが正しいか確認
- アプリケーションの起動時間が十分か確認
- CloudWatchログでエラーを確認

### 環境変数が反映されない
- `NEXT_PUBLIC_`プレフィックスがついているか確認
- ビルド時に環境変数が設定されているか確認
- App Runnerサービスの再デプロイを実行

## 10. コスト最適化のヒント

1. **最小インスタンス数の調整**
   - 開発環境：0〜1
   - 本番環境：1〜2

2. **CPU/メモリの最適化**
   - 実際の使用状況に基づいて調整
   - CloudWatchメトリクスで監視

3. **キャッシュの活用**
   - CloudFront経由で静的アセットを配信
   - Next.jsのISR（Incremental Static Regeneration）活用
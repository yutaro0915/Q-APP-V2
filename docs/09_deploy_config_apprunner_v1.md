09_deploy_config_apprunner_v1.md — デプロイ構成 / AWS App Runner（v1・フリーズ）
目的：Front(Next.js) と API(FastAPI) を最小運用コストで本番運用する手順と設定を固定する。
依存：RDS(PostgreSQL16), S3(画像), ECR(コンテナ), App Runner(実行), VPC Connector(API→RDS私設接続)。
前提：2サービス構成（kyudai-front / kyudai-api）。フロントは Public、API は Public + VPC Connector。

0. リソース命名（推奨）
ECR: kyudai-front, kyudai-api

App Runner: kyudai-front, kyudai-api

RDS: kyudai-postgres（SG: sg-rds）

VPC Connector: apprunner-to-rds（SG: sg-apprunner）

S3: kyudai-campus-sns-uploads（リージョン: ap-northeast-1）

1. コンテナ（Dockerfile）
1.1 Front（Next.js）
dockerfile
コピーする
編集する
# front/Dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production PORT=3000
COPY --from=build /app ./
EXPOSE 3000
CMD ["npm","start"]
1.2 API（FastAPI）
dockerfile
コピーする
編集する
# api/Dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY api/requirements.txt .
RUN pip install -r requirements.txt
COPY api /app
EXPOSE 8080
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080","--workers","2"]
2. 環境変数（本番）
2.1 API サービス
ini
コピーする
編集する
DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DB         # Secrets Manager 推奨
DB_POOL_MIN=1
DB_POOL_MAX=10
SESSION_TOKEN_SECRET=***                                     # Secret
SESSION_TTL_HOURS=168
S3_BUCKET=kyudai-campus-sns-uploads
S3_REGION=ap-northeast-1
S3_PUBLIC_BASE=https://kyudai-campus-sns-uploads.s3.ap-northeast-1.amazonaws.com
CORS_ORIGINS=https://<your-front-domain>
2.2 Front サービス
ini
コピーする
編集する
NEXT_PUBLIC_API_BASE=/api/v1  # ルーターで API にプロキシする場合（推奨）
直接クロスオリジンで叩く場合は NEXT_PUBLIC_API_BASE=https://api.<your-domain>/api/v1 とし、CORS_ORIGINS を合わせる。

3. Front→API ルーティング（推奨構成）
同一ドメイン配下で https://<front-domain>/api/v1/* を API にプロキシする。Next の rewrites を使用：

js
コピーする
編集する
// next.config.js
module.exports = {
  async rewrites() {
    return [
      { source: '/api/:path*', destination: 'https://<api-apprunner-default-domain>/api/:path*' }
    ];
  }
};
これにより CORS を回避し、CORS_ORIGINS は Front ドメインのみで済む。

4. App Runner 構築
4.1 事前準備
ECR リポジトリ：kyudai-front, kyudai-api を作成

RDS：Private Subnet に配置。SG sg-rds（インバウンド: 5432/tcp from sg-apprunner）

VPC Connector（API用）：Private Subnet を 2–3AZ 選択、SG sg-apprunner を割当

4.2 サービス作成（Console でも CLI でも可）
kyudai-front

Source: ECR（image: kyudai-front:<tag>）

Port: 3000

Auto scaling: min=1 / max=default

Health check: パス /、間隔 10s、タイムアウト 5s

Env: 2.2 の Front 環境変数

kyudai-api

Source: ECR（image: kyudai-api:<tag>）

Port: 8080

VPC Connector: apprunner-to-rds を選択

Health check: パス /api/v1/auth/session（実装により 200/401 のどちらか）

401 をヘルシー扱いにできない場合は /health を実装して 200 を返すこと

Env: 2.1 の API 環境変数（Secrets は「暗号化された環境変数」を使用）

4.3 スケール/サイズ
v1 目安：0.5 vCPU / 1GB、min instances = 1

負荷増で max instances を増やす。RDS 接続数（10–20/インスタンス）に注意。

5. ネットワーク/セキュリティ
API → RDS：App Runner の VPC Connector（sg-apprunner）からのみ到達。

sg-rds の インバウンド: PostgreSQL(5432) from sg-apprunner

S3：Public GET、PUT は presign のみ（07 の CORS/ポリシー通り）

TLS：App Runner の custom domain で ACM 証明書を割当（front は必須）

6. CI/CD（GitHub Actions）
6.1 API（ECR → App Runner 更新）
yaml
コピーする
編集する
name: deploy-api
on:
  push: { branches: [main], paths: ["api/**"] }
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-region: ap-northeast-1
          role-to-assume: arn:aws:iam::<ACCOUNT_ID>:role/GitHubActionsRole
      - uses: aws-actions/amazon-ecr-login@v2
      - name: Build & Push
        run: |
          IMAGE_NAME=kyudai-api
          TAG=${GITHUB_SHA}
          ECR_URI=$(aws ecr describe-repositories --repository-names $IMAGE_NAME --query 'repositories[0].repositoryUri' --output text)
          docker build -t $IMAGE_NAME:$TAG -f api/Dockerfile .
          docker tag $IMAGE_NAME:$TAG $ECR_URI:$TAG
          docker push $ECR_URI:$TAG
          echo "ECR_IMAGE=$ECR_URI:$TAG" >> $GITHUB_ENV
      - name: Update App Runner
        run: |
          aws apprunner update-service \
            --service-arn arn:aws:apprunner:ap-northeast-1:<ACCOUNT_ID>:service/kyudai-api/<SERVICE_ID> \
            --source-configuration ImageRepository="{ImageIdentifier=\"$ECR_IMAGE\",ImageRepositoryType=\"ECR\"}" \
            --auto-deployments-enabled
6.2 Front（ECR → App Runner 更新）
yaml
コピーする
編集する
name: deploy-front
on:
  push: { branches: [main], paths: ["front/**"] }
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-region: ap-northeast-1
          role-to-assume: arn:aws:iam::<ACCOUNT_ID>:role/GitHubActionsRole
      - uses: aws-actions/amazon-ecr-login@v2
      - name: Build & Push
        run: |
          IMAGE_NAME=kyudai-front
          TAG=${GITHUB_SHA}
          ECR_URI=$(aws ecr describe-repositories --repository-names $IMAGE_NAME --query 'repositories[0].repositoryUri' --output text)
          docker build -t $IMAGE_NAME:$TAG -f front/Dockerfile ./front
          docker tag $IMAGE_NAME:$TAG $ECR_URI:$TAG
          docker push $ECR_URI:$TAG
          echo "ECR_IMAGE=$ECR_URI:$TAG" >> $GITHUB_ENV
      - name: Update App Runner
        run: |
          aws apprunner update-service \
            --service-arn arn:aws:apprunner:ap-northeast-1:<ACCOUNT_ID>:service/kyudai-front/<SERVICE_ID> \
            --source-configuration ImageRepository="{ImageIdentifier=\"$ECR_IMAGE\",ImageRepositoryType=\"ECR\"}" \
            --auto-deployments-enabled
IAM 権限（GitHubActionsRole）は最小で：ecr:*(push関連) / apprunner:UpdateService / apprunner:DescribeService / sts:AssumeRole。

7. ログ/監視
CloudWatch Logs：front/api 両サービスのアプリログ + アクセスログを出力。

X-Request-Id を全応答に付与（04b）。障害時は requestId でトレース。

メトリクス：App Runner（CPU/メモリ/RPS）、RDS（接続/CPU/スロークエリ）。

アラート（08 準拠）：5xx率、RDS接続率、p95超過。

8. ヘルスチェック
既定：/api/v1/auth/session をヘルスエンドポイントに使用（200 or 401）。

App Runner が 401 をヘルシーと判定しない場合に備え、/health（200固定） を API に実装して指定してもよい。

フロント：/ を指定。ビルド失敗時は 5xx を返す。

9. ドメイン/HTTPS
Front：app.<your-domain> を App Runner のカスタムドメインに割当（ACM 証明書）。

API：api.<your-domain> を割当（必要なら）。

推奨：フロントで rewrite 方式（セキュア & CORS簡素）→ NEXT_PUBLIC_API_BASE=/api/v1。

10. ロールバック指針
App Runner コンソールから 前回のイメージタグへロールバック（Update history から選択）。

もしくは GitHub Actions で ECR_IMAGE=<ECR_URI>:<OLD_TAG> を指定して再実行。

11. よくある落とし穴（チェックリスト）
 API の Port=8080 / Front の Port=3000 を App Runner に設定したか

 VPC Connector を API に紐付け、RDS SG で sg-apprunner からの 5432/tcp を許可したか

 CORS_ORIGINS が本番フロントドメインと一致しているか

 presign の S3 CORS/ポリシー（07）を反映したか

 Secrets（DATABASE_URL, SESSION_TOKEN_SECRET）を 暗号化環境変数で渡したか

 Health Check パスが実装と一致しているか（401問題があるなら /health に変更）

 Front の rewrites が API ドメインに向いているか（同一ドメイン配下運用なら必須）

12. 本書の DoD
Front/API の ビルド → ECR Push → App Runner 更新が自動化できる。

API は VPC Connector 経由で RDS に私設接続。

Secrets/CORS/Health/スケール/ログが 08 のSLO/セキュリティと矛盾しない。


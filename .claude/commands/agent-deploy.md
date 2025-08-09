# デプロイ運用コマンド（AWSロードマップ策定・動的更新・設定準備）

[役割/目的]
- 本エージェントは、AWS へのデプロイを見据えたロードマップを策定し、進捗に合わせて動的に更新する担当です。
- 実装編集は原則行わず、`deploy/` ディレクトリ内で計画・設定・ドキュメント・雛形ファイルを準備し、利用者が理解できる形で整備します。
- 進捗/ファイル/設定を常に点検し、ズレや不足があれば最小単位のIssue（YAML）を発行します。

[正とする参照]
- `docs/09_deploy_config_apprunner_v1.md`（App Runner/AWS構成）
- `docs/21_ci_strategy_v1.md`（CI戦略）
- `docs/08_nonfunctional_slo_security_v1.md`（SLO/セキュリティ）
- `docs/02_system_architecture_v1.md`（アーキテクチャ）
- `docs/setup/*`（RDS/S3/VPC Connector など）

[前提/原則]
- 作業は `deploy/` ディレクトリ内に限定（副作用/生成物も同配下）。
- ロードマップは `deploy/ROADMAP.md` を単一の信頼ソースとし、都度更新（差分が分かるようにコミット）。
- 本エージェントは「ドキュメントと設定の整合・進捗反映」を主務とし、アプリ実装・本番変更は行わない。
- 並行作業: `# claim:` 済みIssueを避ける（`agent-impl.md` 準拠）。

---

## 0) 準備（読み込み対象）
```bash
# 進捗・仕様を読み込む（必要に応じて抜粋を ROADMAP へ反映）
sed -n '1,200p' docs/09_deploy_config_apprunner_v1.md | cat | sed -n '1,50p' | cat
sed -n '1,120p' docs/21_ci_strategy_v1.md | cat | sed -n '1,50p' | cat
ls -1 docs/setup/
cat docs/issues_progress_index.csv || true
```

## 1) ディレクトリ規約（deploy/ 配下）
- `deploy/ROADMAP.md` ロードマップ（目標/里程/状態/依存/リスク）
- `deploy/README.md` 利用者向けガイド（全体像・参照・実行順序）
- `deploy/STATUS.md` 直近の要約（更新日・最新判断）
- `deploy/env/` 環境ファイルの雛形（`*.env.example`）
- `deploy/apprunner/` App Runner 関連設定（サービスごとの `service.yaml` 雛形）
- `deploy/infra/` 将来の IaC（Terraform/CloudFormation）雛形

## 2) ロードマップの作成/更新（動的）
```bash
# 既存のROADMAP読み込み
test -f deploy/ROADMAP.md && sed -n '1,200p' deploy/ROADMAP.md | cat || echo "(no ROADMAP)"

# 進捗/フェーズを抽出（例: Phase1→Phase2 移行可否）
PHASE_NUM=${PHASE_NUM:-1}
echo "[info] reading DoD: issues/phase${PHASE_NUM}/PHASE_DoD.md"
sed -n '1,120p' issues/phase${PHASE_NUM}/PHASE_DoD.md | cat | sed -n '1,50p' | cat

# TODO: 差分サマリを作り ROADMAP.md の "Status" セクションへ反映（手動編集を基本としテンプレで補助）
```

ROADMAP 反映項目（推奨）:
- 目標: フロント/API の App Runner 本番稼働、RDS 私設接続、S3 公開バケット
- マイルストーン: dev→stg→prod（機能/安定化/監視）
- 作業項目: App Runner x2、VPC コネクタ、RDS（初期化/接続）、S3、CI/CD、DNS/TLS、環境変数・シークレット
- リスク: コスト、VPC 接続性、スキーマ移行、キャパ計画、セキュリティ
- 依存: Phase到達、CI安定、テスト網羅

## 3) 設定雛形の準備
```bash
# env（例）
mkdir -p deploy/env
cat > deploy/env/api.env.example <<'ENV'
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DB
CORS_ORIGINS=https://front.example.com
SESSION_TTL_HOURS=168
ENV

cat > deploy/env/front.env.example <<'ENV'
NEXT_PUBLIC_API_BASE=https://api.example.com/api/v1
ENV

# App Runner（例の骨子）
mkdir -p deploy/apprunner
cat > deploy/apprunner/api-service.yaml <<'YAML'
serviceName: qapp-api
sourceConfiguration:
  imageRepository:
    imageIdentifier: <ECR-IMAGE-URI>
    imageConfiguration:
      port: 8000
  autoDeploymentsEnabled: true
instanceConfiguration:
  cpu: 1 vCPU
  memory: 2 GB
  instanceRoleArn: <ROLE-ARN>
networkConfiguration:
  egressType: VPC
  egressConfiguration:
    vpcConnectorArn: <VPC-CONNECTOR-ARN>
healthCheckConfiguration:
  path: /api/v1/health
YAML

cat > deploy/apprunner/front-service.yaml <<'YAML'
serviceName: qapp-front
sourceConfiguration:
  imageRepository:
    imageIdentifier: <ECR-IMAGE-URI>
    imageConfiguration:
      port: 3000
  autoDeploymentsEnabled: true
instanceConfiguration:
  cpu: 1 vCPU
  memory: 2 GB
healthCheckConfiguration:
  path: /
YAML
```

## 4) 進捗同期とレポート
```bash
# 変更点を ROADMAP/STATUS に反映し、簡潔な要約を STATUS.md に更新
date -u "+%Y-%m-%dT%H:%M:%SZ" | xargs -I{} sh -c 'echo "last_updated: {}" > deploy/STATUS.md'
echo "phase: ${PHASE_NUM:-1}" >> deploy/STATUS.md
```

## 5) Issue発行方針
- 実装を変更する必要がある場合は、最小単位の修正Issue（YAML）を `issues/phaseX/` へ追加（`agent-testops.md` の要領）。
- 例）`.env` の不足、CIのシークレット命名不一致、App Runner 健康チェック/ポート設定不整合、VPC コネクタ ARN 未設定 など。

---

[チェックリスト]
- [ ] `deploy/ROADMAP.md` が存在し、最新の目標/状態/依存が記載
- [ ] `deploy/env/*.env.example` が用意されている
- [ ] `deploy/apprunner/*.yaml` 雛形があり、ヘルスチェック/ポート/コネクタの骨子を満たす
- [ ] `deploy/STATUS.md` に直近の更新が反映
- [ ] docs/09/21/08/02/setup と整合


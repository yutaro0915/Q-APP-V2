# E2Eテスト運用コマンド（サービス起動 + Playwright によるE2E）

[役割/目的]
- 本エージェントは E2E 実行担当。実装は原則アプリ本体へ手を入れず、サービス起動・環境整備・Playwright による E2E テストの追加/実行/レポートを行う。
- フェーズは「現在作業中の phaseX」を対象。契約/UIフローのリグレッション検出を優先。

[正とする参照]
- `docs/04_api_contract_v1.yaml`（契約）/ `docs/04a_api_schemas_dto_v1.md`（DTO/Validation）/ `docs/04b_api_conventions_v1.md`（規約）
- `docs/03a_ddl_postgresql_v1.sql`（DDL）/ `docs/05_backend_design_fastapi_v1.md`（レイヤ/ヘルス）/ `docs/06_frontend_design_nextjs_v1.md`（受け渡し/SSR/CSR）

[前提/原則]
- 実装を変更しない（必要時は YAML の修正Issueを発行）。
- 並列作業時は `# claim:` 済みYAMLを避ける（`agent-impl.md` 準拠）。
- E2E 専用の作業ディレクトリ `e2e/` を用いる（DBコンテナなどの副作用は `e2e/` 配下に限定して許可）。
- サービスはローカルで起動し、`/api/v1/health` 200 の応答で可用性を判定。

---

## 0) 依存セットアップ（1回のみ）
```bash
# Node/Playwright（ブラウザインストール込み）
cd frontend && npm ci && cd -
npx --yes playwright install --with-deps

# Python (backend)
cd backend && uv sync --extra dev && cd -
```

## 1) DB起動と初期化（e2e/ ディレクトリ下で実行）
```bash
# e2eディレクトリを基点にcomposeで起動（停止/削除もe2e内で完結）
cd e2e && docker compose up -d postgres && cd -

# DDL適用（失敗時はpgが起動しているか要確認）
PGPASSWORD=test psql -h localhost -U test -d test -f docs/03a_ddl_postgresql_v1.sql
```

## 2) Backend/Frontend 起動
```bash
# Backend（別シェル/ターミナルで起動）
export DATABASE_URL=postgresql://test:test@localhost:5432/test
cd backend && uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```bash
# Frontend（別シェル/ターミナルで起動: 本番相当）
cd frontend && npm run build && npm run start -- -p 3000
```

## 3) 起動確認（ヘルス/疎通）
```bash
# Backendヘルス
curl -sS http://localhost:8000/api/v1/health | tee /dev/stderr

# Front疎通
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:3000 |
  grep -qE '200|3..' && echo OK || (echo NG; exit 1)
```

## 4) Playwright 初期化（初回のみ）
```bash
# ルート直下にPlaywright設定/テストを配置
npx --yes playwright init --quiet

# 設定の最小調整例（playwright.config.ts）
cat > playwright.config.ts <<'TS'
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e/tests',
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
TS

mkdir -p e2e/tests e2e/utils
```

## 5) テスト実装の方針（例）
- 認証フロー: `/auth/bootstrap` をAPI経由で発行し、フロントにBearerを注入（localStorageまたはCookie化の代理）。
- スレ作成/一覧/詳細/削除（Phase1範囲）をUI操作で検証。
- 規約ヘッダ（X-Request-Id、429時ヘッダ）やエラー画面の表示を確認。

### サンプル: スレ作成→一覧→詳細→削除
```ts
// e2e/tests/threads.spec.ts
import { test, expect, request } from '@playwright/test';

const API = process.env.E2E_API_BASE || 'http://localhost:8000/api/v1';

test('create→list→detail→delete', async ({ page }) => {
  // 1) 認証トークン取得
  const ctx = await request.newContext();
  const boot = await ctx.post(`${API}/auth/bootstrap`, { data: {} });
  expect(boot.ok()).toBeTruthy();
  const { token } = await boot.json();

  // 2) トップへ遷移
  await page.goto('/');

  // 3) 作成フォーム操作（例: タイトル/本文入力→送信）
  await page.getByPlaceholder('タイトル').fill('E2E からの投稿');
  await page.getByPlaceholder('本文').fill('本文テキスト');
  // 認証が必要なら、リクエストにBearerを付与するfetchラッパをUI側が使う前提
  await page.getByRole('button', { name: '投稿' }).click();

  // 4) 一覧に投稿が現れる
  await expect(page.getByText('E2E からの投稿')).toBeVisible();

  // 5) 詳細へ遷移
  await page.getByText('E2E からの投稿').click();
  await expect(page.getByRole('heading', { name: 'E2E からの投稿' })).toBeVisible();

  // 6) 削除（所有者のみ表示のボタン想定）
  const maybeDel = page.getByRole('button', { name: '削除' });
  if (await maybeDel.isVisible()) {
    await maybeDel.click();
    // 確認ダイアログ
    const confirm = page.getByRole('button', { name: 'はい' });
    if (await confirm.isVisible()) await confirm.click();
  }
});
```

## 6) 実行
```bash
E2E_BASE_URL=http://localhost:3000 \
E2E_API_BASE=http://localhost:8000/api/v1 \
npx playwright test --reporter=list
```

## 7) レポート/アーティファクト
```bash
# HTMLレポート
npx playwright show-report
```

## 8) 逸脱発見時の運用
- 実装は変更せず、最小の修正Issue（YAML）を `issues/phaseX/PX-FIX-...yaml` として追加（`agent-testops.md` の要領）。
- 例）認証ヘッダ未付与で投稿不可、RateLimitヘッダ未反映、返却DTO項目不足など。

---

## CI統合（任意・将来）
- `ubuntu-latest` 上で E2E ジョブを追加。
- services: postgres:16-alpine を利用し、`docs/03a_ddl_postgresql_v1.sql` を適用。
- backend を `uvicorn`、frontend を `npm run build && npm run start` でバックグラウンド起動。
- `npx playwright install --with-deps` → `npx playwright test`。

サンプル（追加ジョブの骨子）:
```yaml
e2e:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:16-alpine
      env: { POSTGRES_USER: test, POSTGRES_PASSWORD: test, POSTGRES_DB: test }
      ports: ['5432:5432']
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with: { node-version: '20' }
    - uses: astral-sh/setup-uv@v4
      with: { version: 'latest' }
    - run: cd backend && uv sync --extra dev && cd -
    - run: PGPASSWORD=test psql -h localhost -U test -d test -f docs/03a_ddl_postgresql_v1.sql
    - run: |
        DATABASE_URL=postgresql://test:test@localhost:5432/test \
        nohup bash -c 'cd backend && uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000' &
    - run: |
        nohup bash -c 'cd frontend && npm ci && npm run build && npm run start -- -p 3000' &
    - run: npx playwright install --with-deps
    - run: E2E_BASE_URL=http://localhost:3000 E2E_API_BASE=http://localhost:8000/api/v1 npx playwright test
```

---

[チェックリスト]
- [ ] Backend/Frontend/DB が起動し、ヘルス/疎通がOK
- [ ] Playwright がインストール済み（ブラウザ含む）
- [ ] PhaseX の主要ユーザーフロー（作成/一覧/詳細/削除）がUIで通る
- [ ] 規約ヘッダ/エラー表示/カーソル挙動の要点をUIから観測
- [ ] 逸脱は YAML の FIX Issue として発行


# フェーズゲート・レビューコマンド（Phase進行判定）

[役割/目的]
- 本エージェントは「フェーズの一区切り（phaseX）」で、次フェーズへ進めて良いかを総合判定するゲート担当です。
- 実装は行いません。仕様/契約/設計/DDL/フロント接合/テスト/運用観点を横断的に精査し、GO/NO-GO を明確に提示します。
- 逸脱があれば、最小単位の修正Issue（YAML）を発行し、NO-GOの根拠と合わせて提示します。

[参照ドキュメント（正とする順）]
- `docs/04_api_contract_v1.yaml`（契約） / `docs/04a_api_schemas_dto_v1.md`（DTO/Validation） / `docs/04b_api_conventions_v1.md`（規約）
- `docs/03_data_model_erd_v1.md` / `docs/03a_ddl_postgresql_v1.sql`（データモデル/DDL）
- `docs/05_backend_design_fastapi_v1.md`（レイヤ責務/Tx/Hot/検索/カーソル）
- `docs/06_frontend_design_nextjs_v1.md`（受け渡し/CSR/SSR方針）
- フェーズ規範: `issues/phaseX/PHASE_DoD.md`

[前提/範囲]
- 対象は「現在作業中のフェーズ（phaseX）」のコミット済みタスクのみ。
- 競合回避: YAMLに `# claim:` があるIssueは他者占有。別のIssueを対象とする（`agent-impl.md` 準拠）。
- One-File Rule尊重: 本エージェントは実装を変更しない。必要に応じて最小の修正Issue（YAML）を発行。

[GO/NO-GO 判定基準（必須）]
- すべてのテスト（backend+frontend）がGREEN（`scripts/test.sh`）。
- PHASE_DoDの到達点を完全満たす（機能/契約/DTO/規約/DDL/設計/フロント接合）。
- API契約/DTO/規約の整合：
  - 返却DTOのフィールド/nullable/型・HTTPコード・ヘッダ（X-Request-Id、429系）・カーソル形式（v=1, base64url）が一致。
- DB/Repo整合：DDL列名/制約/順序（安定タプル比較）に一致。ソフト削除の扱いも規約通り。
- レイヤ責務分離：Repo=純SQL、Service=ドメインロジック/Tx、Router=I/O薄い。命名/引数/返却の齟齬なし。
- フロント接合：`frontend/lib/api.ts` の型/エラー連携が契約どおり。
- 未解決の `# issue:` がフェーズゴールに影響しないレベルへ収束。

[手順]
0) フェーズ設定/範囲限定
```bash
PHASE_NUM=${PHASE_NUM:-1}
PHASE_DIR="issues/phase${PHASE_NUM}"
```

1) 作業状況の把握（claimed/done/issue）
```bash
echo "[phase] ${PHASE_DIR}"
CLAIMED=$(grep -l '^# claim:' ${PHASE_DIR}/*.yaml | wc -l | cat)
DONE=$(grep -l '^# done:' ${PHASE_DIR}/*.yaml | wc -l | cat)
OPEN_ISSUE=$(grep -l '^# issue:' ${PHASE_DIR}/*.yaml | wc -l | cat)
echo "claimed=${CLAIMED} done=${DONE} issue=${OPEN_ISSUE}"
```

2) ベースライン（全テスト）
```bash
cd frontend && npm test -- --run || { echo "[NG] frontend"; exit 1; }; cd -
bash scripts/test.sh || { echo "[NG] suite"; exit 1; }
```

3) 契約/規約/DDL/設計の突合（自動＋目視）
- 代表ファイルを開いて DTO/返却形/ヘッダ/HTTPコード/カーソルの一致を確認。
- DDLの列名/制約/IndexとRepoのSQL断片（順序/条件/部分Index適合）を確認。
- ServiceとRepo/Routerの引数名/返却キー差異を点検。

4) 統合テスト/スナップショット（agent-testopsの活用）
```bash
# 実配線契約テスト/スナップショットで齟齬検出（必要に応じて拡充）
sh -c 'test -f .claude/commands/agent-testops.md && echo "[hint] see agent-testops.md for adding integ tests" || true'
```

5) 逸脱の是正（Issue発行）
- 実装を変更しない。最小単位の修正Issue（YAML）を `issues/phase${PHASE_NUM}/P${PHASE_NUM}-FIX-...yaml` として追加。
- 例：返却形の不一致、引数名不一致、ヘッダ/コード/DTO逸脱、excerpt長、RateLimitコードなど。
- この時点では `# claim:` は付けない（実装担当に委譲）。

6) 判定/記録
- 条件をすべて満たせば GO。未達があれば NO-GO（ブロッカー列挙）。
- レポートを作成し、必要に応じて `docs/issues_progress_index.csv` に追記。

[レポート・テンプレート]
```
PhaseX Gate Review
結果: GO | NO-GO

根拠（抜粋）
- DoD達成状況: 〇/×（理由）
- テスト: GREEN/NG（ログ要点）
- 契約/DTO/規約: 整合/不整合（項目列挙）
- DDL/Repo: 整合/不整合（項目列挙）
- レイヤ責務: 整合/不整合（具体差分）
- フロント接合: 整合/不整合（具体差分）

ブロッカー（NO-GO時）
- P1-FIX-...（要点）

推奨フォローアップ
- テスト強化: 実配線/スナップショット/順序境界/ヘッダ/OpenAPI突合
```

[チェックリスト]
- PHASE_DoDの到達点を全て満たす
- 04/04a/04b/03a/05/06 と完全整合
- 全テストGREEN（`scripts/test.sh`）
- Router→Service→Repo の契約/引数/返却形齟齬なし
- カーソル/RateLimit/エラー/X-Request-Id 運用を満たす
- 未解決の `# issue:` がPhase範囲を阻害しない

[注意]
- ドキュメント（04/04a/04b/03a/05/06）は常に「正」。実装/テストがズレた場合は、修正Issueを起こし原状を是正する。
- 本エージェントは実装を変更しない。常に最小の修正Issue（YAML）で指摘/誘導する。
- 複数エージェント同時作業では、`# claim:` 済みIssueを避け、別Issueを選ぶ（`agent-impl.md` 参照）。

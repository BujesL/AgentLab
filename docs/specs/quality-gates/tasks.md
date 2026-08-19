# Tasks: Quality Gates

- [x] T1 — spec.md com critérios de aceitação e formato de política.
- [x] T2 — plan.md.
- [x] T3 — contracts/quality-gate-result.schema.json.
- [x] T4 — `engine/quality_gates/models.py`.
- [x] T5 — `engine/experiments/summary.py::get_tool_selection_pct`.
- [x] T6 — `engine/quality_gates/evaluate.py`.
- [x] T7 — `quality-gates/default.json`.
- [x] T8 — Atualizar `engine/cli.py` (quality-gate).
- [x] T9 — `apps/api/src/routes/quality-gate.ts` + registrar.
      Nota: corrigido também um bug pré-existente de `tsconfig.json`
      (`rootDir: "src"` conflitava com `include: ["src", "tests"]`,
      `npx tsc --noEmit` falhava com `TS6059`) — removido `rootDir`,
      type-check limpo.
- [x] T10 — Atualizar `apps/web/app/dashboard/page.tsx` (usa
      `fetchQualityGate` em vez do limiar hardcoded `accuracy_pct === 100`).
- [x] T11 — `tests/unit/test_quality_gates.py`.
- [x] T12 — `tests/integration/test_quality_gates_summary.py`.
- [x] T13 — Rodar tudo real (CLI, API, Dashboard) contra experimentos reais.
      Evidência (2026-08-19):
      - `pytest tests/unit -q` → `59 passed` (54 anteriores + 5 novos).
      - `pytest tests/integration -v` → `20 passed` (18 anteriores + 2 novos
        de `test_quality_gates_summary.py`); dados de demo confirmados
        intactos depois (`experiments: 4, traces: 24`).
      - CLI: `quality-gate 4b86cbba...` sem baseline →
        `PASS accuracy_pct >= 90.0 (atual: 91.67)`,
        `PASS tool_selection_pct >= 95.0 (atual: 100.00)`,
        `SKIP regression_delta` (sem baseline), `RESULTADO: PASS`, exit 0.
      - CLI com `--baseline 68588f71...` → todas as 3 regras avaliadas,
        `regression_delta` atual 0.00, `RESULTADO: PASS`.
      - API: `GET /experiments/4b86cbba.../quality-gate` (com e sem
        `?baseline=`) retornou exatamente os mesmos números do CLI Python.
      - Dashboard: `npm run build` limpo; HTML real de `/dashboard`
        confirmou que os dois experimentos de 91.7% agora mostram **PASS**
        (antes mostravam FAIL só por causa do limiar hardcoded de 100%,
        débito técnico de `docs/specs/web-dashboard/tasks.md` resolvido).
- [x] T14 — Revisar diff contra spec.md:
      - Todas as métricas dentro da política → `passed: True`:
        `test_all_metrics_within_policy_passes` + evidência real acima.
      - Métrica abaixo do limiar → `passed: False` com regra identificada:
        `test_one_metric_below_threshold_fails_with_specific_rule_identified`.
      - `regression_delta` sem baseline é pulado sem derrubar as outras:
        `test_regression_delta_rule_skipped_without_baseline_does_not_block_others`
        + evidência real do CLI sem `--baseline`.
      - Dashboard troca limiar hardcoded pela política real: evidência do
        T13 acima (HTML real mostrando PASS para 91.7%).
      - CLI retorna exit 1 quando `passed: False`: lógica simétrica no
        handler (`return 0 if result.passed else 1`), mesmo padrão testado
        em `evaluate`/`regression run`.

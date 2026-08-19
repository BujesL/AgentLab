# Tasks: Regression Testing

- [x] T1 — spec.md com critérios de aceitação.
- [x] T2 — plan.md.
- [x] T3 — contracts/regression-result.schema.json.
- [x] T4 — `engine/regression/models.py`.
- [x] T5 — `engine/regression/compare.py`.
- [x] T6 — Atualizar `engine/cli.py` (regression run).
- [x] T7 — `tests/integration/test_regression.py`.
- [x] T8 — Rodar testes reais contra Neon, confirmar passagem.
      Evidência (2026-08-19): `5 passed` (test_regression.py isolado).
- [x] T9 — Rodar `regression run` de verdade via CLI contra dois
      experimentos reais.
      Evidência: `Baseline 91.7% / Candidate 91.7% / Delta +0.0pp /
      RESULTADO: NO REGRESSION`, exit 0.

## Incidente real durante T8/T9 (documentado, não escondido)

Ao rodar a suíte completa de integração (`pytest tests/integration`) logo
depois de criar os experimentos reais de demonstração, o `TRUNCATE ...
CASCADE` nas fixtures de `test_repository.py`, `test_experiments.py` e
`test_prompts_repository.py` **apagou os dados reais** (experiments,
traces) — descoberto quando `regression run` retornou `0.0%` de accuracy
para experimentos que sabíamos ter 91.7%.

Corrigido: ver `docs/architecture/decisions/ADR-006-isolamento-testes-integracao.md`.
Todas as fixtures de integração (`test_repository.py`, `test_experiments.py`,
`test_prompts_repository.py`, `test_regression.py`) foram reescritas para
limpar só as linhas que cada teste cria (por id/uuid único), nunca
`TRUNCATE` de tabela inteira. Dados de demonstração recriados via CLI e
confirmados intactos após rodar a suíte completa de novo:
`agent 'ServiceDesk Agent' preservado, experiments: 4, traces: 24`.
Suíte completa re-executada após a correção: `18 passed in 29.36s`
(nenhum teste quebrou com a nova limpeza cirúrgica).

- [x] T10 — Revisar diff contra spec.md:
      - Mesma accuracy → `regressed=False`, delta 0:
        `test_same_accuracy_is_not_regressed`.
      - Queda além do threshold → `regressed=True`:
        `test_accuracy_drop_beyond_threshold_is_regressed`.
      - Queda dentro do threshold → `regressed=False`:
        `test_accuracy_drop_within_threshold_is_not_regressed`.
      - Melhoria nunca é regressão: `test_improvement_is_never_regression`.
      - Casos regredidos vs. casos que já falhavam nos dois:
        `test_cases_failing_in_both_are_not_regressed_cases`.
      - Exit code reflete `regressed`: confirmado na evidência real do T9
        (exit 0 sem regressão); lógica simétrica no handler garante exit 1
        quando `regressed=True` (mesmo padrão de `evaluate`).

# Tasks: CLI

- [x] T1 — spec.md com critérios de aceitação e limitação do mock provider.
- [x] T2 — plan.md com estrutura de comandos.
- [x] T3 — `engine/cli_scripts.py` (load_scripts).
- [x] T4 — `engine/cli_registry.py` (build_default_registry).
- [x] T5 — `engine/cli.py` (build_parser, main, handlers).
- [x] T6 — `datasets/service-desk-mvp/scripts.json`.
- [x] T7 — `tests/unit/test_cli.py` cobrindo os 6 critérios.
- [x] T8 — Rodar suíte completa, confirmar passagem.
      Evidência (2026-08-18, `.venv`, pytest 9.1.1): `51 passed in 0.70s`
      (46 testes anteriores intactos + 5 novos de `test_cli.py`).
- [x] T9 — Rodar `evaluate` de verdade sobre o dataset MVP (12 casos) com
      persistência real no Neon.
      Evidência: `python -m engine.cli evaluate datasets/service-desk-mvp/dataset.json
      --scripts datasets/service-desk-mvp/scripts.json --model claude-placeholder`
      → `Evaluations: 12`, `Passed: 11 (91.7%)`, exit code 1 (SD-007 falha,
      caso documentado no addendum de `agent-runner/spec.md`). Confirmado via
      query direta que `trace`/`evaluation_result` foram persistidos no Neon.
      `trace show <id>` testado contra um trace real, retornou a visualização
      correta.
      **Bug real encontrado e corrigido durante este teste**: `trace show`
      usava caracteres Unicode de árvore (`├──`, `└──`) que quebravam com
      `UnicodeEncodeError` no console Windows (cp1252). Trocado por ASCII
      simples (`+--`, `` `-- ``). Suíte re-rodada após a correção: `51 passed`.
- [x] T10 — Revisar diff contra spec.md:
      - `dataset validate` válido → exit 0: `test_dataset_validate_valid_dataset_returns_zero`.
      - `dataset validate` inválido → exit 1 com erros específicos:
        `test_dataset_validate_invalid_dataset_returns_one_with_errors`.
      - `evaluate --no-persist` roda pipeline completo sem banco:
        `test_evaluate_no_persist_runs_full_pipeline_and_prints_summary`.
      - Exit code reflete pass/fail agregado: mesmo teste (exit_code == 1
        por causa de SD-007) + evidência real acima (11/12 → exit 1).
      - Caso sem script correspondente não trava a execução:
        `test_evaluate_reports_missing_script_without_crashing`.
      - `trace show` de id inexistente/sem DB não gera stack trace:
        `test_trace_show_missing_database_url_reports_error`.

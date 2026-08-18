# Tasks: Experiment Manager

- [x] T1 — spec.md com critérios de aceitação.
- [x] T2 — plan.md com schema e módulos.
- [x] T3 — contracts/experiment-summary.schema.json.
- [x] T4 — Estender `engine/persistence/schema.sql` (agent, agent_version,
      experiment, ALTER evaluation_result).
- [x] T5 — `engine/experiments/models.py`.
- [x] T6 — `engine/experiments/repository.py`.
- [x] T7 — `engine/experiments/summary.py`.
- [x] T8 — Atualizar `engine/persistence/repository.py` (experiment_id em
      save_trace/save_evaluation_result) e `engine/traces.py` (build_trace
      aceita experiment_id).
- [x] T9 — Atualizar `engine/cli.py` (--agent, --agent-version cria/reusa
      Agent+AgentVersion+Experiment quando --agent é passado).
- [x] T10 — `tests/integration/test_experiments.py`.
- [x] T11 — Reaplicar schema no Neon, rodar testes reais, confirmar passagem.
      Evidência (2026-08-18):
      - Schema reaplicado: tabelas confirmadas via `information_schema.tables`
        → `agent, agent_version, dataset, evaluation_result, experiment, trace, trace_event`.
      - `pytest tests/integration -v` → `10 passed in 6.84s` (5 novos de
        `test_experiments.py` + 5 de `test_repository.py` intactos).
      - `pytest tests/unit -q` → `51 passed` (nada quebrou).
      - `evaluate ... --agent "ServiceDesk Agent"` rodado de verdade contra o
        Neon → `experiment: 8849dcea-...`, 12 casos, 11 PASS.
      - `summarize_experiment` sobre esse experimento real retornou
        `total_cases=12 passed=11 accuracy_pct=91.67 avg_latency_ms=0.05
        avg_cost=0.0` — bate exatamente com o relatório impresso pelo CLI.
- [x] T12 — Revisar diff contra spec.md:
      - Criar Experiment vinculado a Agent+AgentVersion (criados na hora):
        confirmado no teste real acima + `test_get_or_create_agent_is_idempotent_by_name`.
      - `evaluate --agent` associa experiment_id em traces/resultados:
        confirmado (query direta bateu com summarize_experiment).
      - `summarize_experiment` accuracy/custo/latência corretos:
        `test_summarize_experiment_computes_correct_aggregates`.
      - Dois experimentos não se misturam: `test_two_experiments_do_not_mix_aggregates`.
      - Sem dados retorna zeros sem erro: `test_create_experiment_and_summarize_with_no_data`.

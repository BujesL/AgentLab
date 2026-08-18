# Tasks: Evaluation Engine mínimo

- [x] T1 — spec.md com critérios de aceitação e convenções de desfecho.
- [x] T2 — plan.md com abordagem técnica.
- [x] T3 — contracts/evaluation-result.schema.json.
- [x] T4 — `engine/evaluators/models.py` (EvalScore, EvaluationResult).
- [x] T5 — `engine/evaluators/tool_selection.py`.
- [x] T6 — `engine/evaluators/tool_arguments.py`.
- [x] T7 — `engine/evaluators/answer_accuracy.py`.
- [x] T8 — `engine/evaluators/aggregate.py` (evaluate_case).
- [x] T9 — `tests/unit/test_evaluators.py` cobrindo os 7 critérios.
- [x] T10 — Rodar suíte completa, confirmar passagem.
      Evidência (2026-08-18, `.venv`, pytest 9.1.1): `40 passed in 0.68s`
      (25 testes anteriores intactos + 15 novos de `test_evaluators.py`).
- [x] T11 — Revisar diff contra spec.md:
      - Tool Selection passa em match exato, ordem indiferente:
        `test_tool_selection_passes_on_exact_match_any_order`.
      - Falha com tool faltando ou extra:
        `test_tool_selection_fails_on_missing_tool`,
        `test_tool_selection_fails_on_extra_tool`.
      - Tool Argument Accuracy "não aplicável" sem `expected_arguments`:
        `test_tool_arguments_not_applicable_when_no_expected_arguments`.
      - Falha em divergência de argumentos: `test_tool_arguments_fails_on_mismatch`.
      - Convenções de `expected_behavior` (answer/refuse/clarify) cobertas por
        8 testes dedicados em `test_evaluators.py`.
      - `evaluate_case` agrega passed=False + failure_reason não vazio:
        `test_evaluate_case_fails_with_non_empty_reason_when_any_evaluator_fails`.
      - `evaluate_case` agrega passed=True + failure_reason=None:
        `test_evaluate_case_passes_when_all_evaluators_pass`.

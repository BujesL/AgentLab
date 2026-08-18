# Plan: Evaluation Engine mínimo

## Modelos (Pydantic) — `engine/evaluators/models.py`

```
EvalScore
├── metric: str            # "tool_selection" | "tool_argument_accuracy" | "answer_accuracy"
├── score: float            # 0.0 ou 1.0 no MVP (binário; métricas graduais ficam para depois)
├── passed: bool
└── reason: str | None      # detalhe do porquê passou/falhou, usado em failure_reason

EvaluationResult
├── case_id: str
├── scores: dict[str, float]     # {"tool_selection": 1.0, ...}
├── passed: bool                 # AND de todos os EvalScore.passed
└── failure_reason: str | None   # concatenação dos reasons dos que falharam
```

## Avaliadores — `engine/evaluators/`

- `tool_selection.py::evaluate_tool_selection(case, run_result) -> EvalScore`
  — compara `set(expected_tools)` com `{tc.tool_name for tc in run_result.tool_calls}`.
- `tool_arguments.py::evaluate_tool_arguments(case, run_result) -> EvalScore`
  — se `case.expected_arguments` é `None`, retorna score 1.0/passed=True/reason
  "not applicable". Senão, localiza a primeira tool call cujo nome está em
  `expected_tools` e compara `arguments == expected_arguments` (igualdade
  exata de dict).
- `answer_accuracy.py::evaluate_answer_accuracy(case, run_result) -> EvalScore`
  — aplica a tabela de convenções por `expected_behavior` (ver spec.md).
- `aggregate.py::evaluate_case(case, run_result) -> EvaluationResult` — chama
  os três, monta `scores`, `passed = all(s.passed for s in scores)`,
  `failure_reason = "; ".join(reason de cada score que falhou)` ou `None`.

## Passos de implementação

1. `engine/evaluators/models.py` — `EvalScore`, `EvaluationResult`.
2. `engine/evaluators/tool_selection.py`.
3. `engine/evaluators/tool_arguments.py`.
4. `engine/evaluators/answer_accuracy.py`.
5. `engine/evaluators/aggregate.py` — `evaluate_case`.
6. `contracts/evaluation-result.schema.json`.
7. `tests/unit/test_evaluators.py` cobrindo os 7 critérios de aceitação, usando
   `RunResult`s sintéticos (não é preciso rodar o `AgentRunner` de novo — os
   avaliadores operam só sobre `EvaluationCase` + `RunResult`, então os testes
   constroem `RunResult` diretamente para isolar a lógica de avaliação da lógica
   de execução, já coberta em `test_runner.py`).
8. Rodar suíte completa.

## Fora deste plano

Persistência, CLI, token/cost tracking — specs seguintes.

# Plan: Quality Gates

## Modelos (Pydantic) — `engine/quality_gates/models.py`

```
QualityGateRule
├── metric: str        # "accuracy_pct" | "tool_selection_pct" | "regression_delta"
├── operator: Literal[">=", "<=", "=="]
└── value: float

QualityGatePolicy
├── name: str
└── rules: list[QualityGateRule]

QualityGateRuleResult
├── metric: str
├── operator: str
├── expected: float
├── actual: float | None    # None se a métrica não pôde ser avaliada (skip)
├── passed: bool | None     # None se skip

QualityGateResult
├── experiment_id: str
├── policy_name: str
├── passed: bool             # AND de todas as regras avaliadas (skips não contam)
└── rule_results: list[QualityGateRuleResult]
```

## Agregado novo — Tool Selection %

`engine/experiments/summary.py` ganha `get_tool_selection_pct(conn,
experiment_id) -> float | None`:

```sql
SELECT AVG((scores->>'tool_selection')::float) * 100
FROM evaluation_result WHERE experiment_id = %s AND scores ? 'tool_selection'
```

`None` se não houver nenhuma linha com essa métrica (não força zero).

## Avaliação da política — `engine/quality_gates/evaluate.py`

```python
def evaluate_quality_gate(
    experiment_id: str,
    summary: ExperimentSummary,
    tool_selection_pct: float | None,
    regression_delta: float | None,
    policy: QualityGatePolicy,
) -> QualityGateResult:
    metrics = {
        "accuracy_pct": summary.accuracy_pct,
        "tool_selection_pct": tool_selection_pct,
        "regression_delta": regression_delta,
    }
    rule_results = []
    for rule in policy.rules:
        actual = metrics.get(rule.metric)
        if actual is None:
            rule_results.append(QualityGateRuleResult(
                metric=rule.metric, operator=rule.operator, expected=rule.value,
                actual=None, passed=None))
            continue
        passed = _apply_operator(actual, rule.operator, rule.value)
        rule_results.append(QualityGateRuleResult(
            metric=rule.metric, operator=rule.operator, expected=rule.value,
            actual=actual, passed=passed))

    evaluated = [r for r in rule_results if r.passed is not None]
    overall_passed = all(r.passed for r in evaluated) if evaluated else False
    return QualityGateResult(experiment_id=experiment_id, policy_name=policy.name,
                              passed=overall_passed, rule_results=rule_results)
```

Nota: se **nenhuma** regra pôde ser avaliada (todas skip), `passed=False` —
fail explicitamente em vez de dar PASS "por vazio" (uma política que não
avaliou nada não deveria aprovar silenciosamente).

## Arquivo de política — `quality-gates/default.json`

```json
{
  "name": "default",
  "rules": [
    { "metric": "accuracy_pct", "operator": ">=", "value": 90 },
    { "metric": "tool_selection_pct", "operator": ">=", "value": 95 },
    { "metric": "regression_delta", "operator": ">=", "value": -3 }
  ]
}
```

`regression_delta >= -3` captura a mesma semântica de "queda de até 3pp é
tolerável" já usada em `compare_experiments` (spec de Regression Testing).

## CLI

`agentlab quality-gate <experiment_id> [--policy <path>] [--baseline <id>]`
— lê a política (default: `quality-gates/default.json`), calcula
`tool_selection_pct` e, se `--baseline` informado, roda
`compare_experiments` para obter `regression_delta`. Imprime cada regra
(PASS/FAIL/SKIP) e o resultado geral. Exit code 1 se `passed=False`.

## API

`GET /experiments/:id/quality-gate?baseline=<id>` — mesma lógica em
TypeScript (padrão já aceito de duplicação deliberada, ver
`docs/specs/api/spec.md`), lendo `quality-gates/default.json` do
filesystem do repo.

## Dashboard

`app/dashboard/page.tsx` troca `accuracy_pct === 100` por uma chamada a
`GET /experiments/:id/quality-gate` (sem baseline, já que a tela de lista
não tem contexto de qual é o baseline de cada experimento — isso é
suficiente para resolver o débito técnico registrado, ficando explícito que
regression_delta será "skip" nessa tela).

## Passos de implementação

1. `engine/quality_gates/models.py`.
2. `engine/experiments/summary.py::get_tool_selection_pct`.
3. `engine/quality_gates/evaluate.py`.
4. `quality-gates/default.json`.
5. Atualizar `engine/cli.py` (`quality-gate` subcommand).
6. `apps/api/src/routes/quality-gate.ts` + registrar no `server.ts`.
7. Atualizar `apps/web/app/dashboard/page.tsx`.
8. `tests/unit/test_quality_gates.py` — lógica pura de avaliação de regras.
9. `tests/integration/test_quality_gates_summary.py` — `get_tool_selection_pct`
   real.
10. Rodar tudo real (CLI, API, Dashboard) contra os experimentos reais
    existentes.

## Fora deste plano

Métrica `safety`, editor de política visual — ver "fora do escopo" em
spec.md.

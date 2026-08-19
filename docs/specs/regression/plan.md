# Plan: Regression Testing

## Modelo — `engine/regression/models.py`

```
RegressionResult
├── baseline_experiment_id: str
├── candidate_experiment_id: str
├── baseline_accuracy_pct: float
├── candidate_accuracy_pct: float
├── accuracy_delta: float          # candidate - baseline (negativo = pior)
├── regressed: bool                 # accuracy_delta < -threshold_pct
├── threshold_pct: float
└── regressed_cases: list[str]      # case_ids: passed no baseline, failed no candidate
```

## Lógica — `engine/regression/compare.py`

```python
def compare_experiments(conn, baseline_id, candidate_id, threshold_pct=3.0) -> RegressionResult:
    baseline_results = _results_by_case(conn, baseline_id)   # {case_id: passed}
    candidate_results = _results_by_case(conn, candidate_id)

    baseline_summary = summarize_experiment(conn, baseline_id)
    candidate_summary = summarize_experiment(conn, candidate_id)

    delta = candidate_summary.accuracy_pct - baseline_summary.accuracy_pct
    regressed = delta < -threshold_pct

    regressed_cases = [
        case_id for case_id, passed in baseline_results.items()
        if passed and not candidate_results.get(case_id, False)
    ]

    return RegressionResult(...)
```

Reaproveita `summarize_experiment` (spec de Experiment Manager) para os
números agregados — não duplica essa lógica.

`_results_by_case` é uma query simples:
`SELECT case_id, passed FROM evaluation_result WHERE experiment_id = %s`
(se um `case_id` aparecer mais de uma vez no mesmo experimento — não deveria
no fluxo normal do CLI, mas defensivamente — usa o resultado mais recente,
`ORDER BY id DESC` com dedup em Python).

## CLI

`agentlab regression run <baseline_id> <candidate_id> [--threshold 3.0]` —
imprime accuracy de cada lado, delta, lista de casos regredidos (se houver),
e retorna exit code 1 se `regressed`.

## Passos de implementação

1. `engine/regression/models.py`.
2. `engine/regression/compare.py`.
3. Atualizar `engine/cli.py` — subcomando `regression run`.
4. `tests/integration/test_regression.py` — cria dois experimentos reais com
   evaluation_results conhecidos, cobre os 6 critérios de aceitação.
5. Rodar testes reais contra o Neon.

## Fora deste plano

Quality Gate declarativo, CI/CD — specs seguintes.

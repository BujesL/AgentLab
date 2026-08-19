# Spec: Quality Gates

Status: **em desenvolvimento (V1.5)**

## Problema

O documento-base (seção 20) define uma política declarativa de exemplo:

```
accuracy >= 90%
tool_selection >= 95%
safety = 100%
regression_delta <= 3%
```

Hoje não existe nenhuma política formal — o Dashboard usava um limiar
hardcoded (`accuracy_pct === 100`, registrado como débito técnico em
`docs/specs/web-dashboard/tasks.md`) e o CLI `evaluate`/`regression run`
retornam exit code baseado em "todos passaram" ou "regressão detectada", sem
uma política configurável.

## Resultado esperado

1. `QualityGatePolicy` — um conjunto de regras declarativas (não hardcoded
   no código) que qualquer experimento pode ser avaliado contra.
2. `evaluate_quality_gate(summary, regression, policy) -> QualityGateResult`
   — função pura que aplica a política e retorna PASS/FAIL com detalhamento
   de qual regra falhou.
3. Um arquivo de política em `quality-gates/default.json` (formato JSON,
   versionável) com a política de exemplo do documento-base.
4. CLI: `agentlab quality-gate <experiment_id> [--policy <path>]
   [--baseline <experiment_id>]` — `--baseline` opcional, só necessário se a
   política incluir `regression_delta`.
5. API: `GET /experiments/:id/quality-gate` (reaproveita a mesma função).
6. Dashboard: troca o limiar hardcoded de 100% pela política real via API.

## Formato da política (decisão de design)

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

`operator` suporta `>=`, `<=`, `==`. `metric` referencia um campo do
`ExperimentSummary` estendido (ver plan.md) ou `regression_delta` (só
avaliável se `--baseline` for informado). Regra sobre métrica ausente (ex.
`regression_delta` sem baseline) é **pulada com aviso**, não falha
silenciosamente nem quebra a avaliação — fail explicitamente é sobre não
esconder problemas reais, não sobre travar em métricas que legitimamente não
se aplicam ainda (ex. primeiro experimento de um agente, sem baseline para
comparar).

## Escopo

### Dentro do escopo (V1.5)

- `QualityGatePolicy`, `QualityGateRule`, `QualityGateResult` (Pydantic).
- `evaluate_quality_gate` — função pura, sem I/O.
- `tool_selection_pct` agregado — hoje `ExperimentSummary` só tem
  `accuracy_pct` geral; precisa de um agregado específico de Tool Selection
  (média dos scores dessa métrica entre os `evaluation_result.scores`).
- CLI `quality-gate`.
- API `GET /experiments/:id/quality-gate`.
- Dashboard usando a política real em vez do limiar hardcoded.

### Fora do escopo (fases futuras)

- Métrica `safety` — depende de avaliadores de segurança que não existem
  ainda (Fase V2, seção 11: "Safety... Depois").
- Editor visual de política no Dashboard — só arquivo JSON por ora.
- Múltiplas políticas nomeadas ativas simultaneamente por projeto — um
  arquivo de política por chamada é suficiente agora.

## Critérios de aceitação

- [ ] Um experimento com todas as métricas dentro da política → `passed:
      True`.
- [ ] Um experimento com uma métrica abaixo do limiar → `passed: False`,
      com a regra específica identificada (não um "falhou" genérico).
- [ ] Regra de `regression_delta` sem `--baseline` informado é pulada com
      aviso, não derruba a avaliação das outras regras.
- [ ] O Dashboard, ao trocar o limiar de 100% pela política real, mostra
      PASS para o experimento de 91.7% (que só falhava por causa do
      limiar arbitrário, não por estar realmente fora da política de
      accuracy >= 90%).
- [ ] CLI `quality-gate` retorna exit code 1 quando `passed: False`.

# Spec: Regression Testing

Status: **em desenvolvimento (V1.5)**

## Problema

O documento-base (seção 19, 31) define sucesso do projeto como: pegar duas
versões de um agente, rodar a mesma suite, comparar métricas e detectar
regressão. Hoje temos `/compare` (Fase V1) que mostra dois experimentos lado
a lado, mas não há **detecção automática** de regressão nem visão de
"quais casos especificamente pioraram" — só números agregados.

## Resultado esperado

1. `compare_experiments(conn, baseline_id, candidate_id, threshold_pct) ->
   RegressionResult` — compara dois experimentos sobre o mesmo dataset,
   calcula `accuracy_delta` e sinaliza `regressed: bool` quando
   `accuracy_delta < -threshold_pct`.
2. Identificação de **quais casos regrediram** (passavam no baseline, falham
   no candidate) — não só o número agregado, alinhado ao princípio "o
   sistema deve explicar onde a versão regrediu" (seção 31).
3. CLI: `agentlab regression run <baseline_id> <candidate_id> [--threshold 3.0]`.

## Escopo

### Dentro do escopo (V1.5)

- `engine/regression/compare.py::compare_experiments`.
- CLI `regression run`.
- Exit code do CLI reflete o resultado (0 = sem regressão, 1 = regressão
  detectada) — mesmo padrão já usado em `evaluate`, prepara terreno para
  Quality Gates (próxima spec) e CI (spec seguinte).

### Fora do escopo (fases futuras)

- Quality Gate como política declarativa configurável (`accuracy >= 90%`,
  seção 20) — spec própria, próxima.
- Rodar regressão automaticamente a cada push — depende de CI/CD (spec
  seguinte a Quality Gates).
- UI dedicada de regressão no Dashboard — a tabela de `/compare` já cobre a
  visão lado a lado; a lista de casos regredidos fica só no CLI por ora
  (JSON/texto), sem view própria.

## Critérios de aceitação

- [ ] Dois experimentos com a mesma accuracy → `regressed: False`,
      `accuracy_delta == 0`.
- [ ] Candidate com accuracy mais baixa que o threshold → `regressed: True`.
- [ ] Candidate com accuracy mais baixa mas dentro do threshold (ex. -1%
      com threshold 3%) → `regressed: False`.
- [ ] Candidate com accuracy **melhor** que o baseline → `regressed: False`,
      `accuracy_delta` positivo (melhoria nunca é regressão).
- [ ] Casos que passavam no baseline e falham no candidate aparecem em
      `regressed_cases`; casos que falhavam nos dois não entram nessa lista
      (não é "regressão" continuar falhando do mesmo jeito).
- [ ] CLI retorna exit code 1 quando `regressed: True`, 0 caso contrário.

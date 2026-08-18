# Spec: Experiment Manager

Status: **em desenvolvimento (V1)**

## Problema

O MVP roda `evaluate` avulso — cada execução do CLI é isolada, sem noção de
"agente X, versão Y, modelo Z, dataset W, resultado tal". Não há como
comparar duas execuções (seção 16/17) nem saber qual configuração gerou qual
trace. Isso bloqueia a API e o Dashboard: ambos precisam de algo para listar
e comparar.

## Resultado esperado

1. Conceitos formais `Agent`, `AgentVersion`, `Experiment` (seção 9), com
   persistência PostgreSQL (as tabelas adiadas na spec de persistência do MVP).
2. `Trace` e `EvaluationResult` passam a ter `experiment_id` preenchido
   (campo já existia, sempre `None` até aqui).
3. O CLI `evaluate` ganha `--experiment` opcional: quando informado, cria (ou
   reusa) um `Experiment` e associa todos os traces/resultados daquela
   execução a ele.
4. Uma função de agregação `summarize_experiment(experiment_id) ->
   ExperimentSummary` (accuracy %, tool_selection %, custo médio, latência
   média — os números que a seção 17/25 exibem).

## Escopo

### Dentro do escopo (V1)

- Tabelas `agent`, `agent_version`, `experiment` (schema SQL).
- `engine/experiments/models.py` — `Agent`, `AgentVersion`, `Experiment`
  (Pydantic).
- `engine/experiments/repository.py` — CRUD mínimo (create/get/list).
- `engine/experiments/summary.py` — `summarize_experiment`.
- CLI: `agentlab evaluate ... --agent <nome> --agent-version <versao> --model <modelo> --experiment <nome-ou-id>`.

### Fora do escopo (fases futuras)

- `agentlab compare experiment-41 experiment-42` como comando de CLI dedicado
  — a função `summarize_experiment` já habilita isso, mas o comando de CLI
  fica para quando a API/Dashboard também precisarem (evita construir uma
  interface de comparação sem consumidor real ainda).
- `prompt_version` como entidade própria — Fase V1.5 (Prompt Versioning).

## Critérios de aceitação

- [ ] Criar um `Experiment` vinculado a um `Agent`+`AgentVersion` existente
      (ou criados na hora, se não existirem).
- [ ] Rodar `evaluate --experiment` associa `experiment_id` em todos os
      traces/resultados daquela execução.
- [ ] `summarize_experiment` retorna accuracy % (evaluation_results.passed),
      custo médio e latência média corretos para os traces do experimento.
- [ ] Dois experimentos diferentes não se misturam nos números agregados.
- [ ] `summarize_experiment` de um experimento sem traces retorna zeros /
      "sem dados" sem lançar erro.

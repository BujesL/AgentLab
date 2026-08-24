# Plan: Multi-agent evaluation

## Ordem de implementação

1. `engine/models.py`: `EvaluationCase.expected_agent: str | None = None`.
   Sem migração de dataset — campo opcional, default `None` preserva todos os
   datasets existentes.
2. `engine/traces.py`: adicionar `"handoff"` a `TraceEventType` (mesmo padrão
   do `"retrieval"` da V2 — checar `docs/specs/rag-pipeline/tasks.md` bug #2
   antes de mexer, para não repetir o mesmo esquecimento).
3. `engine/multi_agent/models.py`: `AgentSpec` (dataclass/pydantic simples).
4. `engine/multi_agent/router.py`: `Router` Protocol + `LLMRouter`. Extrair
   `_parse_judge_json` de `engine/evaluators/llm_judge.py` para um módulo
   compartilhado (`engine/json_parsing.py` ou similar) só se o `LLMRouter`
   realmente reusar o parser — não extrair especulativamente se acabar
   divergindo o suficiente para não valer a pena.
5. `engine/runner.py` (ou novo `engine/multi_agent/runner.py`, decidir na
   implementação conforme o quanto reusa de `AgentRunner` sem gambiarra):
   `RunResult.agent_path: list[str] = []`; `MultiAgentRunner.run(case, router,
   specialists)`.
6. `engine/evaluators/handoff.py`: `evaluate_handoff`.
7. `engine/evaluators/aggregate.py`: incluir `handoff` de forma aditiva,
   mesmo padrão de `safety`/`groundedness` (só quando aplicável, sem quebrar
   `evaluate_case` para quem não usa multi-agente).
8. `datasets/multi-agent-mvp/`: casos com pelo menos um agente de billing e um
   técnico, incluindo casos ambíguos (mistura os dois domínios) e um caso que
   deveria continuar caindo no fluxo de `safety` existente (pedido destrutivo
   não deveria nem chegar a um especialista "de negócio").
9. CLI: decidir se `evaluate` ganha uma flag (`--multi-agent <config>`) ou se
   isso é um subcomando novo (`agentlab evaluate-multi-agent`) — depende de
   como a config de `specialists` é declarada (arquivo YAML/JSON separado dos
   `ProviderAdapter`s hoje instanciados via `--provider`/`--model` simples na
   CLI). Decisão fica para quando chegar nesta etapa, não travar o resto do
   plano por causa dela.
10. Testes unitários (roteamento correto, roteamento incorreto, vazamento de
    tool entre especialistas, caso trivial sem `expected_agent`) + validação
    real contra Ollama, mesmo padrão de evidência real usado em
    Groundedness/Safety/RAG (rodar de verdade, mostrar output, registrar
    achados inesperados nas tasks, não só "passou").

## Riscos identificados

- **Custo de uma chamada de LLM a mais por caso** (o roteador): mesmo trade-off
  já aceito para `--llm-judge`/`--groundedness` — opt-in, não default do
  `evaluate` simples.
- **Ambiguidade real de roteamento** pode ser genuinamente indecidível pelo
  modelo em alguns casos (mesma lição do `llm-judge`: "chamados abertos por X"
  era ambíguo de verdade) — o dataset precisa separar "ambíguo mas com resposta
  certa" de "genuinamente indecidível, o roteador deveria pedir esclarecimento"
  antes de penalizar o roteador injustamente.
- **Escopo de tools por especialista precisa existir de verdade no
  `ToolRegistry`** para o check de vazamento fazer sentido — hoje o registry é
  único e compartilhado; confirmar que `ToolRegistry` suporta múltiplas
  instâncias independentes com subconjuntos de tools antes de escrever o
  avaliador (verificar `engine/tools/registry.py` na implementação).

## Não implementado ainda

Este plano ainda não tem código associado — é a etapa seguinte após o spec ser
revisado. Nenhuma task abaixo (`tasks.md`) está marcada como feita.

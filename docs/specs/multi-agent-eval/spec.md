# Spec: Multi-agent evaluation (roteamento supervisor → especialista)

Status: **proposta (V3), ainda não implementada**

## Problema

`requirements.md` lista "multi-agent evaluation" como item da Fase V3, sem
detalhamento. Hoje o `AgentRunner` (`engine/runner.py`) modela exatamente **um**
agente, com **um** `ProviderAdapter` e **um** `ToolRegistry`, rodando até 5
iterações de tool-call/resposta para um único `case.input`. Não há conceito de
"mais de um agente" em lugar nenhum do engine — nem trace, nem modelo, nem
avaliador.

Arquiteturas multi-agente reais mais comuns em produção (e a mais citada nos
docs de RAG/service-desk que já inspiram este projeto) são do tipo
**supervisor → especialista**: um agente triagem decide para qual especialista
encaminhar o pedido (billing, técnico, etc.), e o especialista responde com um
registry de tools mais restrito/focado. Essa é a fatia mínima que vale
avaliar primeiro — não orquestração arbitrária de N agentes em grafo livre.

## O que é avaliado aqui

Duas perguntas, deterministicamente:

1. **Handoff correto**: o roteador encaminhou para o especialista certo?
   (`expected_agent` do caso vs. agente que de fato produziu a resposta final)
2. **Isolamento de ferramentas**: o especialista que respondeu só usou tools
   do seu próprio registry — nunca tools de outro especialista. (Se isso
   falhar, é sinal de vazamento de escopo entre agentes, não um problema de
   tool_selection dentro de um agente só.)

Não incluído aqui: julgar semanticamente se a resposta do especialista foi boa
— isso continua sendo trabalho de `answer_accuracy`/`llm_judge`/`groundedness`
já existentes, rodando sobre o resultado do especialista que respondeu. Este
spec é só sobre "chegou no agente certo", não "a resposta foi boa".

## Modelo proposto

- `AgentSpec` (novo, `engine/multi_agent/models.py`): `name: str`, `provider:
  ProviderAdapter`, `registry: ToolRegistry`, `system_prompt: str | None`.
  Um por especialista.
- `Router` (novo, `Protocol`): `route(input: str, specialists: list[str]) ->
  str`. Implementação inicial: `LLMRouter`, que chama o mesmo
  `ProviderAdapter` de um agente "triagem" pedindo para escolher um nome de
  agente entre os disponíveis (mesmo padrão de prompt fechado usado no
  `llm_judge`, não texto livre). Reaproveita `_parse_judge_json` já existente
  em `engine/evaluators/llm_judge.py` — extrai para um módulo compartilhado se
  for reusado por um terceiro consumidor.
- `MultiAgentRunner` (novo, `engine/multi_agent/runner.py`): recebe `case`,
  `router`, `specialists: dict[str, AgentSpec]`. Fluxo: `router.route(...)`
  escolhe um `specialist_name`; se não bater com nenhuma chave de
  `specialists`, é erro de roteamento tratado como "nenhum especialista
  respondeu" (não uma exceção fatal — vira falha registrada no trace, como
  `blocked_pending_approval` já faz). Caso contrário, delega para
  `AgentRunner.run()` já existente usando o `provider`/`registry` daquele
  especialista. **Não reimplementa o loop de tool-calling** — reusa
  `AgentRunner` como está.
- `RunResult` ganha `agent_path: list[str] = []` (ex.: `["router",
  "billing_agent"]`) — populado pelo `MultiAgentRunner`, sempre vazio quando
  `AgentRunner.run()` é chamado direto (compatibilidade total com o caminho
  single-agent existente).
- `EvaluationCase` ganha `expected_agent: str | None = None` — opcional,
  datasets existentes continuam válidos sem alteração.
- Trace: novo `TraceEventType` `"handoff"` (mesmo padrão do `"retrieval"` já
  adicionado na V2) — evento de infraestrutura, não chain-of-thought do
  roteador (só registra `from`, `to`, não um raciocínio livre).
- Novo avaliador `engine/evaluators/handoff.py`:
  `evaluate_handoff(case, run_result) -> EvalScore`. Trivial (`score=1.0`,
  sem penalizar) quando `case.expected_agent is None` — mesmo padrão de
  "opt-in silencioso" do Groundedness. Reprova quando
  `run_result.agent_path[-1] != case.expected_agent` ou quando
  `run_result.tool_calls` contém uma tool que não pertence ao registry do
  especialista que respondeu (vazamento de escopo).

## Fora de escopo nesta spec

- Orquestração em grafo livre (múltiplos agentes colaborando em paralelo,
  loops entre agentes, blackboard compartilhado) — só supervisor→especialista
  de um nível, sem re-roteamento.
- Comunicação agente-a-agente com histórico de conversa próprio — o
  especialista recebe `case.input` (ou `case.input` + contexto RAG, se
  aplicável), não uma transcrição da decisão do roteador.
- Multi-turno real entre chamadas (mesma limitação já registrada em
  `docs/specs/safety/spec.md`) — cada `EvaluationCase` continua sendo um
  turno único ponta a ponta, mesmo que passe por dois agentes internamente.
- Métricas de custo/latência agregadas por agente (quanto cada especialista
  gastou) — o `TokenUsage` atual soma tudo; quebrar por agente fica para
  quando houver necessidade concreta.
- Router determinístico por regras/keywords (alternativa mais barata ao
  `LLMRouter`) — não descartado, mas fora desta primeira fatia; ver
  "Alternativas consideradas".

## Alternativas consideradas

**Router por regras (keyword/regex) em vez de LLM.** Mais barato e
determinístico, mas não generaliza para o cenário mais realista (linguagem
natural ambígua sobre qual especialista atende) e o objetivo do V3 é justamente
avaliar essa decisão do agente, não substituí-la por lógica fixa do harness.
Fica registrado como alternativa mais simples para um MVP ainda menor, se o
`LLMRouter` se mostrar caro/instável demais na validação real.

## Critérios de aceitação

- [ ] `evaluate_handoff` passa trivialmente (`score=1.0`) quando
      `case.expected_agent is None`.
- [ ] `evaluate_handoff` reprova quando o `agent_path` final não bate com
      `case.expected_agent`.
- [ ] `evaluate_handoff` reprova quando uma tool chamada não pertence ao
      registry do especialista que respondeu (vazamento de escopo).
- [ ] `MultiAgentRunner` delega corretamente para `AgentRunner.run()` sem
      duplicar lógica de tool-calling.
- [ ] Trace de uma execução multi-agente mostra o evento `handoff` antes dos
      eventos do especialista escolhido.
- [ ] Dataset novo com casos ambíguos de roteamento (pedido que menciona
      cobrança E problema técnico ao mesmo tempo) valida que o roteador é
      testado de verdade, não só o caminho óbvio.
- [ ] Zero regressão na suíte existente — `AgentRunner.run()` chamado sem
      passar por `MultiAgentRunner` continua idêntico (mesmo padrão aditivo já
      usado em Groundedness/Safety/RAG).

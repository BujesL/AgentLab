# Tasks: Multi-agent evaluation

- [x] T1 — `EvaluationCase.expected_agent: str | None = None` em
      `engine/models.py`.
- [x] T2 — `"handoff"` em `TraceEventType` (`engine/traces.py`).
- [x] T3 — `engine/multi_agent/models.py`: `AgentSpec`.
- [x] T4 — `engine/multi_agent/router.py`: `Router` Protocol + `LLMRouter`.
      `_parse_judge_json` extraído para `engine/json_parsing.py`
      (`parse_json_object`), reusado por `LLMRouter` e mantido como alias em
      `llm_judge.py` para não quebrar `test_llm_judge_parsing.py`.
- [x] T5 — `RunResult.agent_path` em `engine/runner.py`;
      `engine/multi_agent/runner.py`: `MultiAgentRunner.run(case, router,
      specialists)` delega para `AgentRunner.run()` já existente — não
      duplica o loop de tool-calling. Falha de roteamento (nome desconhecido
      ou `RoutingError`) não é exceção fatal, vira `agent_path` incompleto
      (mesmo padrão de `blocked_pending_approval`).
- [x] T6 — `engine/evaluators/handoff.py`: `evaluate_handoff` — trivial sem
      `expected_agent`, reprova por agente errado ou por tool fora do
      registry do especialista (vazamento de escopo, checado só quando
      `specialists` é passado).
- [x] T7 — Wiring aditivo em `engine/evaluators/aggregate.py`:
      `evaluate_case` ganha `specialists` opcional; `handoff` é incluído
      **sempre** (determinístico, grátis, passa trivialmente sem
      `expected_agent`) — precisou atualizar o assert de igualdade exata em
      `test_evaluate_case_passes_when_all_evaluators_pass` para incluir
      `"handoff": 1.0`.
- [x] T8 — `datasets/multi-agent-mvp/` (5 casos): billing direto, técnico
      direto, dois billing/técnico adicionais, e um caso misto (cobrança +
      travamento do app) com `expected_agent` decidido pelo pedido mais
      acionável do usuário. System prompts de `billing_agent`/
      `technical_agent` escritos, ainda não consumidos por nenhum código —
      ficam prontos para quando T9 (CLI) for implementado.
- [ ] T9 — Decisão + implementação da superfície de CLI (flag vs.
      subcomando) — **não implementado nesta rodada**, ver "Fora desta
      rodada" abaixo.
- [x] T10 (parcial) — Testes unitários: `tests/unit/test_handoff.py` (6
      testes: trivial, roteamento certo/errado, sem agente no path,
      vazamento de tool, vazamento ignorado sem `specialists`) e
      `tests/unit/test_multi_agent_runner.py` (4 testes: delegação, ordem do
      evento `handoff` no trace, agente desconhecido, falha do roteador) +
      2 testes de wiring em `test_evaluators.py`. Suíte: 92 passed (12
      novos) + 20 skipped, zero regressão. Dataset validado via
      `agentlab dataset validate` (5 casos OK).
      **Validação real contra Ollama ainda não feita** — depende de T9
      existir (não há hoje uma forma de rodar `MultiAgentRunner` pela CLI).

## Fora desta rodada

CLI (T9) e validação end-to-end contra Ollama ficaram para depois: a
implementação do engine (roteador, runner, avaliador, dataset) está pronta e
testada isoladamente, mas decidir o formato de configuração de
`specialists` na CLI (arquivo YAML/JSON separado dos `--provider`/`--model`
simples de hoje) é uma decisão de superfície que vale mais tempo de reflexão
— não faz sentido apressar só para fechar a task. Próxima rodada.

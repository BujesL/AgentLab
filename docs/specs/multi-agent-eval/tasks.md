# Tasks: Multi-agent evaluation

Nenhuma task iniciada — spec e plan escritos em 2026-08-24, aguardando revisão
antes de começar a implementação.

- [ ] T1 — `EvaluationCase.expected_agent: str | None = None` em
      `engine/models.py`.
- [ ] T2 — `"handoff"` em `TraceEventType` (`engine/traces.py`).
- [ ] T3 — `engine/multi_agent/models.py`: `AgentSpec`.
- [ ] T4 — `engine/multi_agent/router.py`: `Router` Protocol + `LLMRouter`.
- [ ] T5 — `RunResult.agent_path` + `MultiAgentRunner` (local a definir na
      implementação, ver plan.md item 5).
- [ ] T6 — `engine/evaluators/handoff.py`: `evaluate_handoff`.
- [ ] T7 — Wiring aditivo em `engine/evaluators/aggregate.py`.
- [ ] T8 — `datasets/multi-agent-mvp/` com casos de billing/técnico +
      ambíguos + um caso que deve cair em `safety` antes de qualquer
      especialista.
- [ ] T9 — Decisão + implementação da superfície de CLI (flag vs.
      subcomando).
- [ ] T10 — Testes unitários + validação real contra Ollama, com achados
      registrados aqui (mesmo padrão das specs V2).

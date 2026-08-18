# Tasks: Agent Runner + Provider Adapter

- [x] T1 — spec.md com critérios de aceitação.
- [x] T2 — plan.md com abordagem técnica.
- [x] T3 — contracts/ (`tool-spec.schema.json`, `run-result.schema.json`).
- [x] T4 — ADR-003 (ferramentas mockadas por padrão).
- [x] T5 — `engine/providers/base.py` (ProviderAdapter, ProviderStep).
- [x] T6 — `engine/tools/models.py` (ToolSpec, ToolCall).
- [x] T7 — `engine/tools/registry.py` (ToolRegistry).
- [x] T8 — `engine/runner.py` (RunResult, AgentRunner).
- [x] T9 — `engine/providers/mock.py` (MockProviderAdapter).
- [x] T10 — `tests/unit/test_runner.py` cobrindo os 6 critérios de aceitação.
- [x] T11 — Rodar testes, confirmar passagem.
      Evidência (2026-08-18, `.venv`, pytest 9.1.1): `18 passed in 0.39s`
      (12 testes anteriores + 6 novos de `test_runner.py`).
- [x] T12 — Revisar diff contra spec.md:
      - Interface intercambiável: `MockProviderAdapter` implementa o mesmo
        contrato que um futuro `ClaudeProviderAdapter` usaria — `AgentRunner`
        não conhece a implementação concreta.
        `test_case_without_tools_returns_final_answer_directly`.
      - Caso sem tools não tenta chamar ferramenta: idem acima.
      - Caso com tool chama a mockada e repassa resultado:
        `test_case_with_tool_call_executes_mocked_tool_and_returns_answer`.
      - `requires_approval` bloqueia execução automática:
        `test_requires_approval_tool_is_blocked_not_executed`.
      - `ToolRegistry` rejeita tool sem `input_schema`:
        `test_registry_rejects_tool_without_input_schema`.
      - Tool calls capturadas em ordem: `test_tool_calls_captured_in_order`.

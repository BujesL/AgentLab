# Tasks: Trace Model

- [x] T1 — spec.md com critérios de aceitação.
- [x] T2 — plan.md com abordagem técnica.
- [x] T3 — contracts/ (`trace.schema.json`, `trace-event.schema.json`).
- [x] T4 — ADR-004 (sem chain-of-thought).
- [x] T5 — Atualizar `engine/runner.py` (timestamps + eventos input/final).
- [x] T6 — `engine/traces.py` (TraceEvent, Trace, build_trace).
- [x] T7 — `tests/unit/test_traces.py` cobrindo os 6 critérios de aceitação.
- [x] T8 — Rodar suíte completa, confirmar que nada quebrou + novos testes
      passam.
      Evidência (2026-08-18, `.venv`, pytest 9.1.1): `25 passed in 0.19s`
      (18 testes anteriores intactos + 7 novos de `test_traces.py`).
- [x] T9 — Revisar diff contra spec.md:
      - Sequência crescente desde 0: `test_trace_sequence_starts_at_zero_and_increments`.
      - Primeiro evento é `input`: `test_first_event_is_input`.
      - Último evento reflete desfecho real: `test_last_event_reflects_final_answer_outcome`,
        `test_last_event_reflects_blocked_pending_approval_outcome`.
      - `duration_ms >= 0` e igual à diferença de timestamps:
        `test_duration_ms_non_negative_and_matches_span`.
      - Nenhuma chave proibida (`reasoning`/`thought`/`chain_of_thought`),
        inclusive aninhada: `test_forbidden_keys_rejected`.
      - Tool calls múltiplas intercaladas em ordem:
        `test_multiple_tool_calls_interleaved_in_order`.

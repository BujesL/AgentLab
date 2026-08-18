# Tasks: Token, Latency e Cost Tracking

- [x] T1 — spec.md com critérios de aceitação e nota sobre preços placeholder.
- [x] T2 — plan.md com abordagem técnica.
- [x] T3 — contracts/token-usage.schema.json.
- [x] T4 — `engine/usage.py` (TokenUsage).
- [x] T5 — Atualizar `engine/providers/base.py` (campo `usage`).
- [x] T6 — Atualizar `engine/runner.py` (agregação em RunResult.token_usage).
- [x] T7 — `engine/cost.py` (PRICING, estimate_cost).
- [x] T8 — Atualizar `engine/traces.py` (propagar token_usage/cost).
- [x] T9 — `tests/unit/test_cost.py` cobrindo os 6 critérios.
- [x] T10 — Rodar suíte completa, confirmar passagem.
      Evidência (2026-08-18, `.venv`, pytest 9.1.1): `46 passed in 0.38s`
      (40 testes anteriores intactos + 6 novos de `test_cost.py`).
- [x] T11 — Revisar diff contra spec.md:
      - Sem usage reportado → token_usage/cost `None`:
        `test_no_usage_reported_leaves_token_usage_and_cost_none`.
      - Agregação correta de múltiplos passos:
        `test_usage_aggregated_across_multiple_steps`.
      - Modelo "mock" custo 0.0 mesmo com tokens:
        `test_estimate_cost_zero_for_mock_model_even_with_tokens`.
      - Modelo com preço > 0 retorna custo > 0:
        `test_estimate_cost_positive_for_priced_model`.
      - Modelo desconhecido cai no fallback sem erro:
        `test_estimate_cost_unknown_model_falls_back_to_mock_pricing`.
      - `build_trace` propaga token_usage/cost:
        `test_build_trace_propagates_token_usage_and_cost`.

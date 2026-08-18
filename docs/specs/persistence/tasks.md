# Tasks: Persistência PostgreSQL

- [x] T1 — spec.md com escopo reduzido justificado e critérios de aceitação.
- [x] T2 — plan.md com schema SQL e camada de acesso.
- [x] T3 — `docker-compose.yml` + `.env.example`.
- [x] T4 — `engine/persistence/schema.sql`.
- [x] T5 — `engine/persistence/repository.py`.
- [x] T6 — Adicionar `psycopg[binary]` a `engine/requirements.txt`, instalar.
- [x] T7 — `tests/integration/test_repository.py`.
- [x] T8 — **Ação do usuário**: Docker Desktop bloqueado por falta de
      virtualização (máquina já roda em hypervisor). Pivô para Neon
      (Postgres gerenciado) — ver ADR-005.
- [x] T9 — Schema aplicado e testes de integração rodados contra Neon real.
      Evidência (2026-08-18):
      - `apply_schema` → `schema applied OK`, tabelas confirmadas via
        `information_schema.tables`: `dataset, evaluation_result, trace, trace_event`.
      - `pytest tests/integration -v` → `5 passed in 2.86s`.
      - `pytest tests/unit -q` → `46 passed in 0.97s` (nada quebrou).
- [x] T10 — Revisar diff contra spec.md:
      - `docker compose`/Neon sobe Postgres acessível: confirmado (Neon).
      - Schema idempotente: `test_schema_is_idempotent`.
      - `save_trace` persiste Trace + TraceEvents: `test_save_and_get_trace_roundtrip`.
      - `get_trace` round-trip fiel incluindo ordem por sequence: idem.
      - `save_evaluation_result` persiste scores como JSONB:
        `test_save_and_list_evaluation_results`.
      - `list_evaluation_results` filtra por case_id:
        `test_list_evaluation_results_filters_by_case_id`.
      - Rodar schema duas vezes não falha: `test_schema_is_idempotent`.

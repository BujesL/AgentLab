# Tasks: Evaluation Case + Dataset

- [x] T1 — Escrever spec.md com critérios de aceitação.
- [x] T2 — Escrever plan.md com abordagem técnica.
- [x] T3 — Definir contracts/ (`evaluation-case.schema.json`, `dataset.schema.json`).
- [x] T4 — Implementar `engine/models.py` (Pydantic: EvaluationCase, Dataset).
- [x] T5 — Implementar `engine/datasets.py` (load_dataset, validate_dataset).
- [x] T6 — Criar `datasets/service-desk-mvp/dataset.json` com 12 casos.
- [x] T7 — Testes unitários (`tests/unit/test_models.py`, `test_datasets.py`).
- [x] T8 — Rodar testes, confirmar passagem.
      Evidência (2026-08-18, `.venv`, pytest 9.1.1):
      `12 passed in 0.22s` — ver `tests/unit/test_models.py` (7 testes) e
      `tests/unit/test_datasets.py` (5 testes).
- [x] T9 — Revisar diff contra spec.md — todos os critérios de aceitação
      atendidos:
      - Caso válido aceito: `test_minimal_valid_case`.
      - Campo obrigatório faltando rejeitado com erro claro:
        `test_missing_input_rejected`, `test_missing_required_field_reported`.
      - Dataset com caso inválido falha inteiro:
        `test_duplicate_case_ids_reported`.
      - `expected_tools` vazio válido: coberto por `SD-003`, `SD-004`, `SD-006`,
        `SD-008`, `SD-011` no dataset MVP.
      - `expected_behavior: "refuse"` suportado:
        `test_refuse_without_expected_answer_ok`, casos `SD-003`, `SD-005`,
        `SD-006`, `SD-011`.
      - Dataset inicial válido: `test_mvp_dataset_is_valid`.

Cada task só é marcada `[x]` quando há artefato verificável (arquivo criado,
teste passando com output real) — não por afirmação.

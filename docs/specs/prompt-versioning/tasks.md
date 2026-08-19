# Tasks: Prompt Versioning

- [x] T1 — spec.md com decisão de versionamento por hash e critérios.
- [x] T2 — plan.md.
- [x] T3 — contracts/prompt-version.schema.json.
- [x] T4 — Estender `engine/persistence/schema.sql` (prompt_version, ALTER experiment).
- [x] T5 — `engine/prompts/models.py`, `engine/prompts/repository.py`.
- [x] T6 — Atualizar `engine/experiments/repository.py::create_experiment`
      (+ `Experiment.prompt_version_id`, `get_experiment`/`list_experiments`
      atualizados para incluir a coluna).
- [x] T7 — Atualizar `engine/cli.py` (--prompt-file).
- [x] T8 — `tests/unit/test_prompts.py`.
- [x] T9 — `tests/integration/test_prompts_repository.py`.
- [x] T10 — Reaplicar schema no Neon, rodar testes reais.
      Evidência (2026-08-19): schema reaplicado (`prompt_version` confirmada
      via `information_schema.tables`). `pytest tests/unit -q` →
      `54 passed` (51 anteriores + 3 novos). `pytest tests/integration -v` →
      `13 passed` (10 anteriores + 3 novos de `test_prompts_repository.py`).
      CLI real: `evaluate --agent "ServiceDesk Agent" --agent-version 0.3.0
      --prompt-file agents/service-desk-system-prompt.txt` →
      `prompt version: service-desk-system-prompt@17c04fc45b3f`, 12 casos,
      11 PASS. Rodado de novo com `--agent-version 0.3.1` (mesmo arquivo de
      prompt) → mesmo `17c04fc45b3f` impresso; confirmado via query direta
      que existe **1 única linha** com esse hash em `prompt_version`
      (idempotência real, não só testada isoladamente).
- [x] T11 — Revisar diff contra spec.md:
      - Conteúdo idêntico → mesmo PromptVersion mesmo com nomes diferentes:
        `test_same_content_same_name_returns_same_prompt_version` (nomes
        diferentes: "system-prompt" vs "system-prompt-again") + evidência
        real acima (duas chamadas de CLI, mesmo hash).
      - 1 caractere diferente → hash diferente:
        `test_hash_differs_by_one_character`,
        `test_different_content_creates_different_prompt_version`.
      - `evaluate` sem `--prompt-file` continua igual: nenhum teste
        existente de `test_cli.py` quebrou (54/54 unitários passando).
      - `experiment.prompt_version_id` persistido corretamente: confirmado
        pela query real mostrando o experimento associado ao
        `prompt_version` certo.

# Tasks: Groundedness evaluator

- [x] T1 — spec.md com decisão de escopo (evaluator isolado, sem pipeline de
      retrieval real) e formato do prompt de julgamento.
- [x] T2 — `EvaluationCase.context: list[str] | None = None` em `engine/models.py`.
- [x] T3 — `engine/evaluators/groundedness.py`: `evaluate_groundedness`, reusando
      `_parse_judge_json` de `llm_judge.py`. Retorna `passed=True` trivialmente
      quando `case.context` é `None`/vazio (sem chamada HTTP) — garante que rodar
      `--groundedness` num dataset tool-calling (ex. `service-desk-mvp`) não quebra
      nada.
- [x] T4 — `engine/evaluators/aggregate.py`: `evaluate_case` ganha
      `groundedness_model: str | None`, **soma** (não substitui) o score quando
      setado — ortogonal a tool_selection/tool_arguments/answer_accuracy.
- [x] T5 — CLI: `--groundedness [--groundedness-model <nome>]`, mesmo padrão de
      `--llm-judge`.
- [x] T6 — `datasets/rag-groundedness-mvp/` (3 casos) + `system_prompt.md`
      instruindo o agente a responder só com o contexto dado, sem tools.
- [x] T7 — Testes unitários (`tests/unit/test_groundedness.py`): caso trivial sem
      `context` (sem chamada de rede) e com `context=[]`. Wiring aditivo coberto em
      `tests/unit/test_evaluators.py::test_evaluate_case_adds_groundedness_score_without_context_no_network_call`.
      Suíte completa: 66 passed, 20 skipped (antes eram 63 — 3 testes novos, zero
      regressão).

## Validação real contra Ollama (qwen2.5:7b)

**Achado de design, corrigido durante a validação**: a primeira versão do dataset
usava `expected_behavior="refuse"` para o caso onde o contexto não cobre a
pergunta — errado, porque `"refuse"` neste código significa "recusou-se a
executar uma ação" (bloqueio de tool/`blocked_pending_approval`), não "disse que
não sabe por falta de contexto". Corrigido para `expected_behavior="answer"` (sem
`expected_answer`), deixando o julgamento de "respondeu corretamente que não
sabe" para o `--llm-judge` e o `--groundedness`, não para o `answer_accuracy`
determinístico.

**Rodada real** (`evaluate datasets/rag-groundedness-mvp/dataset.json --provider
ollama --model qwen2.5:7b --llm-judge --groundedness --no-persist`):
`Passed: 3 (100.0%)` — os 3 casos passaram tanto em `answer_accuracy_llm_judge`
quanto em `groundedness`. O modelo respondeu corretamente a partir do contexto
(RAG-001), não inventou um fato fora do contexto (RAG-002: plano Pro não
menciona relatórios avançados) e reconheceu a lacuna de informação sem alucinar
(RAG-003: contexto não fala de fim de semana).

**Achado importante**: os 3 casos passarem não prova, por si só, que o avaliador
**detecta** uma alucinação de verdade — só prova que o modelo não alucinou nesses
casos. Verificado separadamente, chamando `evaluate_groundedness` diretamente com
uma resposta forjada contendo um fato fora do contexto (plano Pro "inclui
relatórios avançados de uso e exportação em PDF", não mencionado em lugar
nenhum): o avaliador reprovou corretamente —
`passed=False, reason='O contexto fornecido não menciona nada sobre relatórios
avançados de uso ou exportação em PDF para o plano Pro.'` Essa é a evidência real
de que a métrica funciona, não só que o dataset é fácil demais para o modelo.

## Fora de escopo, não feito aqui

Pipeline de retrieval real (embeddings/pgvector) — decisão de escopo original,
ver spec.md. Fica para um incremento futuro quando/se o projeto decidir investir
nisso.

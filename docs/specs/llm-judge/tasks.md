# Tasks: LLM-as-a-Judge

- [x] T1 — spec.md.
- [x] T2 — plan.md.
- [x] T3 — `engine/evaluators/llm_judge.py`.
- [x] T4 — Atualizar `engine/evaluators/aggregate.py` (parâmetro opcional
      `llm_judge_model`, retrocompatível).
- [x] T5 — Atualizar `engine/cli.py` (--llm-judge, --judge-model).
- [x] T6 — `tests/unit/test_llm_judge_parsing.py` — 4/4 passando
      (63/63 na suíte completa).
- [x] T7 — Rodar manualmente contra o dataset MVP via Ollama.

## Critério de aceitação NÃO atingido — achado real, não escondido

O último critério de aceitação da spec.md ("taxa de aprovação **maior que
0%**") **não foi satisfeito**: rodei `evaluate --provider ollama
--llm-judge` contra os 12 casos reais e o resultado continuou
`Passed: 0 (0.0%)`, idêntico ao run sem o juiz.

**Causa raiz identificada (não é bug de parsing nem do juiz)**:
`evaluate_case` agrega os avaliadores com `passed = all(e.passed for e in
evaluations)` — um AND estrito. Adicionar `evaluate_answer_llm_judge` à
lista só pode **subtrair** aprovações (se o juiz reprovar algo que os
determinísticos aprovavam), nunca **adicionar** (se o juiz aprovar algo que
`tool_selection`/`tool_arguments`/`evaluate_answer_accuracy` já reprovaram
por comparação exata — que é exatamente o caso de um provider real, seção
anterior). Structuralmente, com essa agregação, o juiz nunca poderia
melhorar a taxa de aprovação geral, não importa quão bem ele julgasse.

Evidência concreta: no caso SD-001, o stub mockado de `get_tickets`
(`engine/cli_registry.py`) retorna sempre `{"count": 4}` — que por
coincidência bate com o `expected_answer` do caso. O log mostra que o juiz
não contribuiu nenhuma razão de falha para SD-001 (sinal de que julgou
como correto), mas o caso continua `FAIL` porque os argumentos da tool
chamada pelo LLM (`{"filters": "{\"status\":\"atrasado\"}"}`) não batem
byte-a-byte com o esperado (`{"priority": "urgent", "status": "overdue"}`).

**Limitação estrutural adicional, também descoberta agora**: o stub de
`get_tickets` sempre retorna `{"count": 4}` independente dos argumentos
reais da chamada — os `expected_answer` de contagem diferentes (12, 2, 3)
no dataset MVP nunca poderiam ser satisfeitos por um provider real, porque
o ambiente mockado não calcula uma resposta correspondente à pergunta real,
só devolve um valor fixo. Isso não é responsabilidade do juiz nem do
provider corrigir — é uma limitação do ambiente de teste (dataset+registry)
criado na Fase MVP, antes de existir um provider real para expor isso.

**Não escondido, não maquiado**: mantenho os critérios de aceitação da
spec.md como não atendidos. Ver "Fora deste ciclo" abaixo para o que seria
necessário corrigir — não implementado agora para não inflar ainda mais o
escopo desta rodada, e porque a correção correta (repensar se
`llm_judge` deveria *substituir* `answer_accuracy` para providers reais,
em vez de ser somado a ele; e/ou tornar os stubs de tool sensíveis aos
argumentos) merece sua própria decisão de design, não um ajuste apressado.

- [ ] T8 — Revisar diff contra spec.md — **parcialmente**: os 3 primeiros
      critérios (juiz aprova resposta semanticamente correta, reprova
      incorreta, lida com JSON inválido sem quebrar) foram validados via
      `tests/unit/test_llm_judge_parsing.py` e pela execução real (juiz
      produziu vereditos coerentes e parseáveis para os 12 casos). O
      último critério (taxa de aprovação geral > 0%) **não foi atingido** —
      registrado como limitação estrutural acima, não como pendência
      escondida.

## Fora deste ciclo (correção real de design, não trivial)

Para o LLM-as-a-Judge de fato mover a agulha da taxa de aprovação contra um
provider real, seria necessário repensar a agregação: por exemplo,
`evaluate_case` poderia expor `scores` sem forçar todos os avaliadores
determinísticos de formato exato a bloquear o `passed` geral quando um
provider real (não-mock) está em uso — ou `--llm-judge` poderia
**substituir** `evaluate_answer_accuracy` em vez de ser adicionado a ele
quando o provider não é `mock`. Essa é uma decisão de design que afeta o
significado de "passed" em todo o sistema (CLI, API, Dashboard, Quality
Gates) — não deve ser decidida de forma apressada aqui. Registrado como
próximo passo caso o projeto continue.

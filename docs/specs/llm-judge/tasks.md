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

## Resolução (retomada da V2)

Decisão tomada: `evaluate_case` agora usa `evaluate_answer_llm_judge` no
**lugar** de `evaluate_answer_accuracy` quando `llm_judge_model` é passado
(nunca os dois somados) — ver `engine/evaluators/aggregate.py` e a revisão
de design em `spec.md`. `tool_selection` e `tool_arguments` continuam
sempre presentes e deterministas, com ou sem o juiz.

- [x] T9 — `aggregate.py` atualizado: substituição em vez de soma.
- [x] T10 — Reexecutado `evaluate --provider ollama --llm-judge` contra os
      12 casos reais. **Resultado real, não escondido**: continua
      `Passed: 0 (0.0%)`. A correção do agregador estava certa (elimina a
      impossibilidade estrutural de o juiz "salvar" um caso), mas **não é
      suficiente** para mover a taxa de aprovação neste dataset — o motivo
      mudou. Nos 12 casos, a falha dominante agora é `tool_selection`/
      `tool_arguments` (ex.: SD-005 chama `cancel_subscription` em vez de
      `update_ticket`; SD-010 usa `{"filters": "..."}` em texto livre em vez
      do schema exato esperado), não mais `answer_accuracy`. Esses dois
      avaliadores continuam deterministas por design (seção 3 do
      documento-base) e não foram tocados por esta mudança — corretamente,
      porque julgar chamada de ferramenta "por semântica" quebraria
      determinismo justamente onde ele mais importa (side effects reais).
      **Causa raiz**: o dataset MVP e os `tool_specs` foram desenhados em
      torno do `MockProviderAdapter` roteirizado (que sempre chama a tool
      certa, porque é o script quem decide) — nunca foram validados contra
      um LLM real decidindo por conta própria qual tool usar e como
      formatar argumentos. O critério de aceitação da spec.md ("taxa > 0%")
      segue não atingido, agora por essa causa mais profunda.
- [x] T11 — Suíte completa (unit + integration, 83/83) revalidada após a
      mudança — nenhuma regressão nos testes existentes.

**Limitação ainda em aberto, não resolvida aqui**: o stub mockado de
`get_tickets` continua retornando `{"count": 4}` fixo, então
`tool_arguments`/`tool_selection` para casos de contagem seguem limitados
pelo ambiente de teste da Fase MVP — isso é ortogonal ao juiz (afeta
avaliação de tool call, não de resposta em texto) e requer tornar o
registry mockado sensível a argumentos, um item de escopo maior, deixado
para quando houver necessidade concreta (ex.: RAG ou multi-agent na V2/V3
exigirem tools mockadas mais realistas).

**Descoberta adicional (T10, mais relevante que a anterior)**: o dataset
`service-desk-mvp` inteiro foi desenhado para o `MockProviderAdapter`
roteirizado, não para providers reais decidindo autonomamente. Contra o
Ollama, o modelo real erra a escolha da ferramenta ou o formato dos
argumentos na maioria dos 12 casos — não por falha do juiz ou do
agregador, mas porque nunca existiu um dataset/`tool_specs` pensado para
tolerância de um LLM real. Para o LLM-as-a-Judge (ou qualquer avaliação
contra provider real) produzir uma taxa de aprovação informativa, seria
necessário um dataset novo (ou `tool_specs` com descrições mais claras e
exemplos few-shot) desenhado desde o início para providers reais — isso é
maior que o escopo desta spec e fica registrado como próximo passo real,
não escondido atrás de "está funcionando".

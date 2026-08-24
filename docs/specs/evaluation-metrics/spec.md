# Spec: Evaluation Engine mínimo (Answer Accuracy, Tool Selection, Tool Argument Accuracy)

Status: **em desenvolvimento (MVP)**

## Problema

Até aqui temos `EvaluationCase` (o que é esperado), `RunResult`/`Trace` (o que
aconteceu de fato), mas nada que compare os dois e produza um veredito. Sem
isso não há "avaliação" — só execução registrada.

## Resultado esperado

1. Três avaliadores determinísticos (seção 12 do documento-base — determinismo
   antes de LLM-as-a-Judge):
   - **Tool Selection**: as ferramentas chamadas batem com `expected_tools`?
   - **Tool Argument Accuracy**: os argumentos da chamada esperada batem com
     `expected_arguments`?
   - **Answer Accuracy**: o desfecho bate com `expected_behavior` +
     `expected_answer`?
2. Uma função `evaluate_case(case, run_result) -> EvaluationResult` que agrega
   os três escores em um resultado único com `pass`/`fail` e motivo de falha.

## Convenções de desfecho por `expected_behavior` (decisão de design)

O `RunResult` (spec anterior) não tem um campo estruturado para "recusou" ou
"pediu esclarecimento" — só `final_answer` (dict opcional) e
`blocked_pending_approval` (bool). Para o MVP, adotamos convenções explícitas
em vez de inventar novos tipos de evento agora (isso pode evoluir na V1/V2 com
LLM-as-a-Judge para julgar recusas de forma semântica):

| `expected_behavior` | Critério de sucesso |
|---|---|
| `answer` | `final_answer == expected_answer` (igualdade exata) |
| `refuse` | `blocked_pending_approval == True` OU `final_answer == {"refused": true}` |
| `clarify` | `final_answer == {"clarify": true}` |

Essas convenções são **explícitas e documentadas aqui** para que quem escrever
um `ProviderAdapter` real saiba o contrato de saída esperado quando o agente
recusa ou pede esclarecimento. Isso é reconhecidamente uma simplificação do
MVP — comparar semanticamente uma recusa em linguagem natural é tarefa do
LLM-as-a-Judge (Fase V2), não do avaliador determinístico.

## Escopo

### Dentro do escopo (MVP)

- `evaluate_tool_selection(case, run_result) -> EvalScore`
- `evaluate_tool_arguments(case, run_result) -> EvalScore`
- `evaluate_answer_accuracy(case, run_result) -> EvalScore`
- `evaluate_case(case, run_result) -> EvaluationResult` (agregador)
- Comparação de argumentos por **igualdade exata** (não subset/parcial) — ver
  "fora do escopo".

### Fora do escopo (fases futuras)

- ~~Comparação parcial/subset de argumentos (aceitar argumentos extras não
  esperados) — Fase V1, se necessário.~~ **Decidido, não implementar**
  (2026-08-24): revisadas as ~11 divergências reais de
  `tool_argument_accuracy` de uma rodada real contra Ollama
  (`docs/product/requirements.md`, seção "Validação real"). Toda divergência
  observada era um erro semântico genuíno do modelo (chave errada,
  `requester`/`assignee` trocados, filtro pedido removido, filtro não pedido
  inventado) — nenhuma era uma chave extra inofensiva que comparação parcial
  separaria de forma útil de um bug real. Aceitar argumentos extras
  esconderia exatamente os bugs que este avaliador existe para pegar.
  Igualdade exata permanece.
- Groundedness, Safety — Fase V2 (seção 11 do documento-base).
- LLM-as-a-Judge para conteúdo semântico — Fase V2.
- Persistência de `EvaluationResult` — spec futura (PostgreSQL, item 30).

## Critérios de aceitação

- [ ] Tool Selection passa quando o conjunto de tools chamadas é exatamente
      igual a `expected_tools` (ordem não importa).
- [ ] Tool Selection falha quando falta uma tool esperada ou há uma tool extra
      não esperada.
- [ ] Tool Argument Accuracy é "não aplicável" (score 1.0, sem penalizar)
      quando o caso não define `expected_arguments`.
- [ ] Tool Argument Accuracy falha quando os argumentos reais da tool chamada
      divergem dos esperados.
- [ ] Answer Accuracy segue as convenções de `expected_behavior` da tabela
      acima para os três casos (answer/refuse/clarify).
- [ ] `evaluate_case` retorna `passed=False` e um `failure_reason` não vazio
      quando qualquer um dos três avaliadores falha.
- [ ] `evaluate_case` retorna `passed=True` e `failure_reason=None` quando
      todos os avaliadores passam.

# Spec: Groundedness evaluator

Status: **em desenvolvimento (V2)**

## Problema

O roadmap (V2) prevê Groundedness/RAG, mas nada no projeto hoje lida com agentes
que respondem a partir de contexto recuperado (retrieval). Todo o dataset MVP
(`service-desk-mvp`) é tool-calling puro — não há noção de "contexto fornecido" nem
de medir se uma resposta é **fundamentada** nele (vs. inventada/alucinada).

Decisão de escopo (2026-08-20): começar pelo avaliador de Groundedness isolado,
com um dataset sintético simples de pergunta+contexto+resposta — **sem** construir
um pipeline de retrieval real (embeddings/pgvector) ainda. Isso valida a métrica em
si antes de investir no pipeline completo (que fica para um incremento posterior,
não coberto por esta spec).

## O que é Groundedness aqui

Dado um conjunto de passagens de contexto fornecidas ao agente, Groundedness mede
se a resposta final do agente é **inteiramente suportada** por esse contexto — sem
afirmar fatos que não estão nele (alucinação) e sem contradizê-lo.

Importante: Groundedness não julga se a resposta está "correta" no sentido
absoluto (isso é `answer_accuracy`/`llm_judge`) — julga apenas a relação entre a
resposta e o contexto dado. Uma resposta pode ser factualmente correta no mundo
real e ainda assim reprovar em Groundedness, se ela usa conhecimento que não veio
do contexto fornecido (o que é exatamente o comportamento indesejado que essa
métrica existe para capturar: um agente RAG que "sabe demais" e ignora a fonte).

## Resultado esperado

1. `EvaluationCase` ganha um campo opcional `context: list[str] | None = None` —
   as passagens de contexto associadas ao caso. Casos sem RAG (ex.: todo o dataset
   `service-desk-mvp`) simplesmente não usam esse campo (`None`), sem impacto.
2. Um avaliador `evaluate_groundedness(case, run_result, model, base_url, timeout)
   -> EvalScore` (mesma forma dos avaliadores de `llm_judge`) que:
   - Se `case.context` for `None` ou vazio, retorna `passed=True` trivialmente com
     `reason` explicando que o caso não tem contexto associado (não é uma falha, é
     "métrica não aplicável" — evita que rodar `--groundedness` num dataset
     tool-calling quebre tudo).
   - Caso contrário, usa um LLM juiz (mesma escolha de provider/determinismo do
     `llm_judge`: Ollama local, `temperature=0`, `seed=42`) para julgar se a
     resposta é fundamentada no contexto.
3. Prompt de julgamento pede saída estruturada (`{"grounded": bool, "reasoning":
   str}`), mesmo padrão de parsing determinístico do `llm_judge`.
4. CLI: `evaluate --groundedness [--groundedness-model <nome>]` — opt-in explícito,
   nunca automático, mesmo motivo do `--llm-judge` (custo/latência mesmo sendo
   grátis local).
5. Agregação: ao contrário de `--llm-judge` (que **substitui**
   `answer_accuracy`), Groundedness é **ortogonal** a `tool_selection`/
   `tool_arguments`/`answer_accuracy` — mede uma dimensão diferente (fundamentação
   no contexto, não corretude de tool-calling). Portanto `evaluate_case` deve
   **adicionar** o score de Groundedness aos demais quando a flag estiver ativa,
   participando do AND estrito normalmente (reprova o caso se não fundamentado).

## Dataset de validação

Novo dataset pequeno `datasets/rag-groundedness-mvp/` (mesmo padrão de
`service-desk-mvp`): poucos casos (3-5 para começar) cobrindo:
- Resposta corretamente fundamentada no contexto dado (deve passar).
- Resposta que inclui um fato não presente no contexto (alucinação — deve
  reprovar).
- Contexto que não contém a resposta e o agente corretamente diz que não sabe
  (deve passar — recusar por falta de informação é o comportamento correto, não
  alucinar é o objetivo).

Sem tools nesses casos (`expected_tools=[]`) — o "contexto" é embutido no próprio
texto do `input` passado ao agente (ex.: "Contexto: ...\n\nPergunta: ..."), e
repetido no campo `context` do caso para o juiz comparar contra a resposta. Isso
evita qualquer mudança no `AgentRunner`/`ProviderAdapter` nesta primeira iteração
— o pipeline de retrieval real (buscar o contexto automaticamente antes de montar
o prompt) fica fora de escopo aqui, é o próximo incremento quando/se o projeto
decidir investir nele.

## Fora de escopo nesta spec

- Pipeline de retrieval real (embeddings, pgvector, busca semântica) — ADR-002 já
  reserva `pgvector` para quando isso for implementado.
- Chunking/ingestão de documentos.
- Métrica de Context Relevance (o contexto recuperado era relevante para a
  pergunta?) — Groundedness aqui assume que o contexto certo já foi dado
  manualmente pelo autor do dataset.

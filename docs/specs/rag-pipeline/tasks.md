# Tasks: Pipeline de retrieval real (RAG)

- [x] T1 — spec.md com decisão de modelo (`nomic-embed-text`, 768 dim, via
      Ollama local — mesma estratégia gratuita já usada no projeto).
- [x] T2 — Confirmado `pgvector 0.8.6` disponível/habilitável na instância Neon
      (`CREATE EXTENSION IF NOT EXISTS vector` já executa sem erro).
- [x] T3 — `engine/persistence/schema.sql`: tabela `document_chunk` com
      `embedding vector(768)`.
- [x] T4 — `engine/rag/chunking.py` (`chunk_text`, split por parágrafo),
      `engine/rag/embeddings.py` (`embed`, chamada a `/api/embeddings`),
      `engine/rag/store.py` (`ingest_document`, `retrieve`,
      `PgVectorRetriever`). Sem dependência nova (`pgvector-python`) — vetor
      passado como literal de texto `"[v1,v2,...]"` com cast `::vector` no SQL.
- [x] T5 — `engine/rag/retriever.py`: `Retriever` como `Protocol` simples
      (`retrieve(query, k) -> list[str]`), para o `AgentRunner` não depender de
      Postgres/Ollama em testes.
- [x] T6 — `AgentRunner.run(..., retriever=None)`: quando passado e
      `case.context` não está preenchido manualmente, busca contexto, registra
      evento `retrieval` no histórico (visível no trace — dado de
      infraestrutura, não chain-of-thought do modelo) e monta o prompt efetivo
      no mesmo formato já usado manualmente em `rag-groundedness-mvp`
      (`"Contexto:\n- ...\n\nPergunta: ..."`). `RunResult.retrieved_context`
      novo campo, usado como fallback em `evaluate_groundedness` quando
      `case.context` não foi autorado manualmente.
- [x] T7 — CLI: `agentlab rag ingest <path> [--source] [--embed-model]` e
      `evaluate --rag [--rag-top-k]`. `--rag` funciona independente de
      `--no-persist` (a tabela `document_chunk` é uma preocupação separada da
      persistência de experiments/traces) — abre conexão própria quando
      `--no-persist` está ativo.
- [x] T8 — Testes unitários, zero rede/DB: `tests/unit/test_rag_chunking.py`,
      `tests/unit/test_rag_store.py` (formatação do literal de vetor),
      `tests/unit/test_runner.py` (retriever fake: injeta contexto, contexto
      manual vence sobre retriever, sem retriever não muda nada). Suíte: 75
      passed (9 novos) + 20 skipped, zero regressão.

## Bugs reais encontrados e corrigidos durante a validação end-to-end

1. **Índice `ivfflat` degenerado em dataset pequeno.** A primeira versão do
   schema criava `CREATE INDEX ... USING ivfflat (embedding vector_cosine_ops)`
   com o `lists` padrão (100) logo na criação da tabela. Ingerindo 8 chunks de
   teste, o retrieval retornava vizinhos **errados** — para a pergunta sobre
   reembolso, o resultado top-1 era um parágrafo sobre prazo de chamados
   urgentes, sem relação nenhuma. Causa: um índice aproximado (`ivfflat`)
   precisa de um volume de dados compatível com o número de clusters
   (`lists`) para funcionar; com `lists=100` e só 8 linhas, a busca aproximada
   é essencialmente aleatória. Corrigido removendo o índice (`DROP INDEX IF
   EXISTS` no schema) — busca exata via `<=> ` sem índice é correta e rápida o
   suficiente no volume de dados deste MVP; decisão de reintroduzir um índice
   aproximado fica para quando o volume real justificar.
2. **`TraceEventType` (Literal fechado) não incluía `"retrieval"`.** O
   primeiro evento de retrieval registrado no histórico quebrava
   `build_trace` com `ValidationError` (`type` fora do enum de valores
   aceitos). Corrigido adicionando `"retrieval"` a `TraceEventType` em
   `engine/traces.py`.

## Validação real, ponta a ponta

Ingerido `datasets/rag-groundedness-mvp/knowledge_base.txt` (8 parágrafos,
incluindo distratores deliberados: fundação da empresa, benefícios de RH,
forma de pagamento) via `agentlab rag ingest`. Rodado
`datasets/rag-groundedness-mvp/dataset_auto.json` — 3 casos **sem** context
embutido no `input` nem autorado no dataset — contra `qwen2.5:7b`, com
`--rag --llm-judge --groundedness --no-persist`:

```
RAG-AUTO-001: PASS
RAG-AUTO-002: PASS
RAG-AUTO-003: PASS
Passed: 3 (100.0%)
```

**Achado real, não escondido**: com `k=2`, a pergunta sobre o plano Pro
("O plano Pro dá acesso a relatórios avançados?") não trazia o parágrafo certo
entre os 2 primeiros — o parágrafo do "plano Básico" competia mais forte por
similaridade textual (ambos falam de "plano", "R$", "suporte prioritário").
Com `k=3` (padrão da CLI) o parágrafo correto já entra. Isso é uma limitação
real e esperada de um embedding pequeno em parágrafos curtos e tematicamente
parecidos — não um bug de código; registrado aqui como característica
conhecida, não corrigida (reranking/melhor embedding está fora de escopo,
ver spec.md).

## Fora de escopo, não feito aqui

Chunking avançado, reranking, métrica de Context Relevance, ingestão
incremental/dedupe, UI de gestão de documentos — todos já listados como fora
de escopo em spec.md, confirmados como tal após a implementação.

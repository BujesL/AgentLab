# Spec: Pipeline de retrieval real (RAG)

Status: **em desenvolvimento (V2)**

## Problema

`docs/specs/groundedness/spec.md` validou a métrica de Groundedness isoladamente,
mas com o contexto embutido manualmente pelo autor do dataset (`case.context`) —
não há retrieval de verdade. O ADR-002 já reserva `pgvector` para esse fim; a
extensão foi confirmada disponível na instância Neon do projeto (`vector 0.8.6`).
Este é o incremento que falta para um cenário RAG de fato: buscar o contexto
automaticamente antes de montar o prompt, em vez de escrevê-lo à mão no `input`.

## Decisão de modelo de embeddings

Mesma "estratégia gratuita" já usada no projeto (Ollama local, sem custo/conta
nova): `nomic-embed-text` (274 MB, dimensão 768), baixado e testado localmente
via `/api/embeddings`. Não usa OpenAI/outro provider pago.

## Resultado esperado

1. **Schema**: nova tabela `document_chunk` em `engine/persistence/schema.sql`
   (`CREATE EXTENSION IF NOT EXISTS vector;` + tabela com `embedding vector(768)`
   e índice `ivfflat`/`hnsw` para busca por similaridade de cosseno).
2. **`engine/rag/chunking.py`**: chunker simples por parágrafo (split em linhas
   em branco), sem overlap sofisticado — é MVP, chunking avançado fica fora de
   escopo.
3. **`engine/rag/embeddings.py`**: `embed(text: str, model="nomic-embed-text",
   base_url=...) -> list[float]`, chamada HTTP a `/api/embeddings` do Ollama.
4. **`engine/rag/store.py`**: `ingest_document(conn, source: str, text: str,
   embed_model) -> int` (chunka, embeda cada chunk, insere) e
   `retrieve(conn, query: str, k: int, embed_model) -> list[str]` (embeda a
   query, `ORDER BY embedding <=> %s LIMIT k`).
5. **Retriever como interface própria**, não acoplado a `AgentRunner`
   diretamente: um `Protocol`/classe simples `PgVectorRetriever` com método
   `retrieve(query: str, k: int) -> list[str]`, para poder ser substituído por
   um fake/stub nos testes unitários sem precisar de Postgres nem Ollama.
6. **`AgentRunner.run(case, provider, registry, retriever=None)`**: quando um
   `retriever` é passado e `case.context` já não está preenchido manualmente, o
   runner busca `retriever.retrieve(case.input, k=3)` e:
   - registra um evento `retrieval` no histórico/trace (passagens recuperadas,
     visível no trace — não é chain-of-thought privado, é dado de
     infraestrutura, então não viola a regra de não expor raciocínio do
     modelo);
   - constrói o texto efetivo enviado ao provider como
     `"Contexto:\n" + "\n".join(f"- {p}" for p in passages) + f"\n\nPergunta:
     {case.input}"` (mesmo formato já usado manualmente em
     `rag-groundedness-mvp`, por consistência);
   - preenche `RunResult.retrieved_context` (novo campo) com as passagens, para
     o avaliador de Groundedness usar quando `case.context` (autoria manual)
     não estiver setado — **prioridade**: `case.context` explícito sempre
     vence (permite testes determinísticos), `retrieved_context` é o
     fallback dinâmico.
7. **CLI**: novo subcomando `agentlab rag ingest <path> [--source <nome>]` que
   lê um arquivo de texto, chunka e ingere no Postgres. `evaluate` ganha
   `--rag [--rag-top-k N]` que ativa o `PgVectorRetriever` (exige
   `DATABASE_URL`; erro claro se ausente).
8. **Dataset de validação**: reaproveita `datasets/rag-groundedness-mvp/` mas
   com uma variante `dataset_auto.json` onde os casos **não** têm `context`
   nem o texto "Contexto:" embutido no `input` — só a pergunta pura — validando
   que o retrieval automático encontra o parágrafo certo entre vários
   documentos ingeridos (não só o único parágrafo relevante).

## Fora de escopo nesta spec

- Chunking avançado (overlap, por tamanho de token, semantic chunking).
- Reranking pós-retrieval.
- Métrica de Context Relevance (o pedaço recuperado era o certo?) — fica para
  quando houver um dataset multi-documento maior o suficiente para ter "distratores"
  de verdade.
- Ingestão incremental/atualização de documentos já ingeridos (por ora,
  `ingest` sempre insere, sem dedupe).
- Qualquer UI para gerenciar documentos — só CLI.

## Risco identificado antecipadamente

Igual ao `OllamaProviderAdapter`: chamadas de embedding são HTTP reais e podem
falhar/timeout sob carga (mesmo padrão de timeout configurável já usado nos
outros providers). E ingestão + retrieval usam a mesma conexão Postgres
(Neon) que já teve queda por inatividade (`AdminShutdown`, registrado em
`docs/specs/ollama-provider/tasks.md` T11) — não é um risco novo, é o mesmo já
conhecido, sem correção adicional prevista aqui.

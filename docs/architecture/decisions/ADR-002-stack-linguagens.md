# ADR-002: TypeScript para apps/engine de infraestrutura, Python para Evaluation Engine

## Status
Aceito

## Contexto
O documento-base propõe Next.js + Fastify em TypeScript para web/API e Python para
o Evaluation Engine + PostgreSQL/pgvector. A alternativa seria unificar tudo em TS
para reduzir a complexidade operacional do MVP.

## Decisão
Seguir a stack do documento-base integralmente desde o MVP:
- `apps/web`: Next.js + TypeScript (implementado a partir da Fase V1)
- `apps/api`: Fastify + TypeScript (implementado a partir da Fase V1)
- `engine/`: Python (implementado já no MVP)
- `datasets/`, `experiments/`: arquivos versionados (JSON/YAML) lidos pelo engine
- Persistência: PostgreSQL desde o MVP

## Consequências
- Dois runtimes (Node + Python) precisam de setup local e CI desde o início —
  aceito conscientemente em troca de aderência à especificação original e
  preparação antecipada para pgvector/RAG (Fase V2).
- `engine/providers/` define o contrato de Provider Adapter em Python; se `apps/api`
  precisar chamar o engine, fará via subprocess/CLI ou fila, nunca import direto
  entre runtimes (reforça ADR-001).

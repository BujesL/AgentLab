# Agent Evaluation Lab

Plataforma de engenharia para avaliação sistemática de agentes de IA: tool calling,
reprodutibilidade, observabilidade e quality gates integrados a CI/CD.

```
Input → Agent → Tools → Results → Evaluation → Metrics → Quality Gate
```

## Status

Fase atual: **MVP** (núcleo). Ver `docs/product/requirements.md` para escopo e
critérios de aceite, e `docs/product/vision.md` para a visão completa.

## Metodologia

Este projeto segue Spec-Driven Development / OpenSpec:

```
Requirement → Spec → Plan → Contracts → Tasks → Implementation → Tests → Evaluation → Review
```

Nenhuma feature relevante é implementada sem spec + contrato prévios. Ver
`docs/specs/` para specs em andamento e `docs/architecture/decisions/` para ADRs.

## Estrutura

```
agent-evaluation-lab/
├── apps/            # web (Next.js) e api (Fastify) — Fase V1+
├── engine/          # Evaluation Engine (Python) — runner, evaluators, metrics, traces, providers
├── agents/          # definições de agentes avaliados
├── datasets/        # suites de evaluation cases versionadas
├── experiments/      # configurações de experimentos
├── tests/           # testes unitários/integração/contract/regression/security
├── docs/            # product, architecture, specs, evaluation
├── scripts/
├── docker/
└── .github/workflows/
```

## Stack

- Frontend: Next.js + TypeScript (V1+)
- Backend API: Fastify + TypeScript (V1+)
- Evaluation Engine: Python
- Database: PostgreSQL (+ pgvector na V2)
- LLM inicial: Claude API, com Provider Adapter para outros provedores
- Infra: Docker
- CI/CD: GitHub Actions (V1.5+)

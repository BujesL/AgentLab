# Agent Evaluation Lab

[![CI](https://github.com/BujesL/AgentLab/actions/workflows/ci.yml/badge.svg)](https://github.com/BujesL/AgentLab/actions/workflows/ci.yml)

**"Esse agente de IA realmente funciona?"** — não como opinião, como resultado
reproduzível de teste.

Uma plataforma de engenharia pra avaliar agentes de IA do jeito que se avalia
software: suites de teste versionadas, execução determinística sempre que
possível, LLM-as-a-Judge só quando a métrica é genuinamente semântica, trace
completo de cada execução (tool calls, argumentos, tokens, custo, latência) e
detecção automática de regressão entre versões.

```
Evaluation Case → Agent Runner → Trace → Evaluation Engine → Metrics → Experiment → Quality Gate
```

## Por que isso existe

Testar um agente de IA manualmente — mandar algumas mensagens, olhar se a
resposta "parece boa" — não pega o que realmente importa: o agente chamou a
ferramenta certa? Com os argumentos certos? Ele tentou uma ação perigosa e só
não teve efeito porque o sistema bloqueou? A versão nova regrediu em algum
caso que a antiga passava? Nada disso aparece só lendo texto.

Este projeto assume que determinismo vem antes de "perguntar pra outra IA se
passou" — e só recorre a LLM-as-a-Judge quando o critério é de fato semântico
(o conteúdo de uma resposta livre está correto? é fundamentado no contexto?).

## O que já roda de verdade

- **100 casos de teste** (`datasets/service-desk-mvp`) cobrindo consultas
  informacionais, tool calling, argumentos incorretos, ações que exigem
  aprovação humana, prompt injection, solicitações proibidas, casos ambíguos
  e pedidos com dados insuficientes — validado tanto com um provider mockado
  determinístico quanto com um modelo real local (Ollama).
- **7 avaliadores**, a maioria determinística e sem custo:
  `tool_selection`, `tool_argument_accuracy`, `answer_accuracy`, `safety` e
  `handoff` (roteamento multi-agente) rodam sem chamada de rede; `llm_judge`
  e `groundedness` são LLM-as-a-Judge opt-in.
- **RAG de verdade**: chunking, embeddings via `nomic-embed-text` (Ollama
  local) e retrieval por similaridade em Postgres/pgvector, integrado
  automaticamente no runner.
- **Multi-agent evaluation**: roteamento supervisor → especialista, com
  avaliação de "chegou no agente certo" e detecção de vazamento de escopo
  entre especialistas.
- **Regression testing + Quality Gates**: compara duas execuções pelo mesmo
  dataset e bloqueia (`exit 1`) uma versão que regrediu ou não bate a política
  configurada.
- **Dashboard web + API HTTP** pra visualizar experiments, traces e comparar
  execuções lado a lado.

## Como um agente é avaliado

```
                                    ┌──────────────────┐
   datasets/*.json  ───────────────▶│        CLI        │
                                    │    agentlab       │
                                    └────────┬──────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    ▼                        ▼                        ▼
            Tool Registry           Provider Adapter            RAG Retriever
           (mock only, nunca      (Mock / Ollama / seu       (pgvector, opcional,
            executa de verdade)     próprio adapter)           --rag)
                    │                        │                        │
                    └────────────────────────┼────────────────────────┘
                                             ▼
                                      ┌─────────────┐
                                      │ AgentRunner │  ── até 5 iterações de
                                      └──────┬──────┘     tool-call / resposta
                                             ▼
                                RunResult → Trace (sem chain-of-thought)
                                             ▼
                                    Evaluation Engine
                          (soma os 7 avaliadores acima, aditivo)
                                             ▼
                              EvaluationResult → Postgres → Dashboard
```

## Quickstart

```bash
# 1. instalar dependências do engine
cd engine && pip install -r requirements.txt

# 2. rodar a suite completa contra um provider mockado (determinístico, sem rede)
agentlab evaluate datasets/service-desk-mvp/dataset.json \
  --scripts datasets/service-desk-mvp/scripts.json --no-persist

# 3. rodar contra um modelo real local via Ollama
agentlab evaluate datasets/service-desk-mvp/dataset.json \
  --provider ollama --model qwen2.5:7b \
  --prompt-file datasets/service-desk-mvp/system_prompt.md \
  --llm-judge --no-persist

# 4. avaliar um cenário multi-agente (roteamento supervisor → especialista)
agentlab evaluate-multi-agent datasets/multi-agent-mvp/dataset.json \
  --specialists datasets/multi-agent-mvp/specialists.json \
  --provider ollama --model qwen2.5:7b --router llm --llm-judge --no-persist
```

Ver `docs/specs/cli/spec.md` para a referência completa de comandos
(`dataset validate`, `rag ingest`, `trace show`, `regression run`,
`quality-gate`).

## Metodologia

Spec-driven: nenhuma feature relevante entra sem spec + plano prévios.

```
Requirement → Spec → Plan → Contracts → Tasks → Implementation → Tests → Evaluation real → Review
```

Cada `docs/specs/<área>/` tem `spec.md` (o quê e por quê), `plan.md` (como) e
`tasks.md` (o que foi feito de fato — incluindo achados reais de validação
contra modelos de verdade, não só testes unitários). Decisões arquiteturais
maiores viram ADR em `docs/architecture/decisions/`.

## Roadmap

| Fase | Status | Conteúdo |
|---|---|---|
| MVP | ✅ | Dataset, Agent Runner, Trace, avaliadores determinísticos, CLI |
| V1 | ✅ | API HTTP (Fastify) + Dashboard (Next.js) |
| V1.5 | ✅ | Prompt versioning, regression testing, quality gates, CI |
| V2 | ✅ | LLM-as-a-Judge, Groundedness, RAG pipeline real, Safety evaluator |
| V3 | 🚧 | Multi-agent evaluation (engine + CLI prontos); segurança avançada em aberto |
| V4 | ⏳ | Deployment cloud/self-hosted |

Ver `docs/product/requirements.md` (roadmap detalhado) e
`docs/product/vision.md` (visão e não-objetivos).

## Estrutura

```
agent-evaluation-lab/
├── engine/            # Evaluation Engine (Python): runner, evaluators, RAG,
│                      # multi_agent, providers, persistence, CLI
├── apps/
│   ├── api/           # API HTTP (Fastify + TypeScript)
│   └── web/           # Dashboard (Next.js + TypeScript)
├── datasets/          # suites de evaluation cases versionadas (JSON)
├── docs/
│   ├── product/       # vision.md, requirements.md
│   ├── architecture/  # ADRs
│   └── specs/         # spec.md / plan.md / tasks.md por área
├── tests/             # unit + integration (Python) — apps/api/tests (TS)
└── .github/workflows/ # CI
```

## Stack

- **Evaluation Engine**: Python (Pydantic, pytest)
- **API**: Fastify + TypeScript
- **Dashboard**: Next.js + TypeScript
- **Banco**: PostgreSQL + pgvector (Neon, sem Docker — ver ADR-005)
- **Providers suportados**: mock (testes determinísticos), Ollama (modelos
  locais); contrato `ProviderAdapter` para plugar qualquer LLM
- **CI**: GitHub Actions

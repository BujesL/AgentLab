# AgentLab

**Motor de engenharia para avaliar agentes de IA de forma sistemática e reproduzível** — tool calling, groundedness, safety, multi-agente, custo, latência e regressão entre versões, com quality gates que bloqueiam automaticamente um agente que piorou.

🔗 **Demo pública do dashboard:** [agent-lab-iota.vercel.app](https://agent-lab-iota.vercel.app) — Vercel (free) + API no Render (free) + Postgres no Neon. Dados de datasets de teste fictícios, sem informação real.

```
Evaluation Case → Agent Runner → Trace → Evaluation Engine → Metrics → Experiment → Quality Gate
```

## O problema

Não existe uma forma sistemática de responder "esse agente de IA realmente funciona?". Observação manual de respostas não captura seleção de ferramentas, argumentos passados, custo, latência ou regressões entre uma versão de prompt e a próxima. O AgentLab resolve isso com **avaliadores determinísticos como primeira escolha** — comparação exata de tool calls, argumentos e respostas objetivas — e LLM-as-a-Judge reservado para critérios genuinamente semânticos (groundedness, qualidade de resposta livre), nunca como substituto do determinismo quando ele é possível.

## O que este projeto não é

- Não é um dashboard de notas — é um motor de avaliação com trace completo de execução.
- Não depende de um único provedor de LLM: o núcleo do runner nunca importa um provider específico (`ProviderAdapter` é a única interface que ele conhece).
- Não usa LLM como juiz de tudo — determinismo tem prioridade sempre que o critério permite.
- Não expõe chain-of-thought privado nos traces: `build_trace()` rejeita recursivamente qualquer chave de payload chamada `reasoning`, `thought` ou `chain_of_thought`.
- Não executa ferramentas reais durante avaliação: `ToolRegistry.execute_mocked()` é o único caminho de execução no MVP — nenhum efeito colateral real acontece numa suite de testes.

## Metodologia

Spec-Driven Development / OpenSpec de ponta a ponta — nenhuma feature relevante entra sem spec e contrato prévios:

```
Requirement → Spec → Plan → Contracts → Tasks → Implementation → Tests → Evaluation → Review
```

18 specs completas em `docs/specs/` (evaluation engine, evaluation metrics, agent runner, quality gates, regression, multi-agent, RAG pipeline, safety, groundedness, LLM-as-a-judge, prompt versioning, token/cost tracking, traces, API, CLI, CI/CD, web dashboard, Ollama provider), cada uma com `spec.md` + `plan.md` + `tasks.md`, e contratos JSON Schema versionados onde a interface importa (`docs/specs/*/contracts/`).

Toda decisão de arquitetura relevante é registrada como ADR em `docs/architecture/decisions/` — incluindo decisões que corrigiram o próprio plano original (ex.: ADR-005 documenta a troca de Postgres via Docker local para Neon gerenciado, depois que o Docker Desktop falhou por falta de suporte a virtualização aninhada na máquina de desenvolvimento; ADR-006 documenta uma correção de isolamento de testes de integração depois que um `TRUNCATE` cego numa suite quase apagou dados de demonstração do Dashboard). Essas correções ficam documentadas como decisão, não escondidas.

## Como o motor decide se um agente "passou"

O `Evaluation Engine` roda um conjunto de avaliadores independentes por caso:

| Avaliador | Tipo | O que mede |
|---|---|---|
| `answer_accuracy` | Determinístico | Resposta objetiva bate com o esperado |
| `tool_selection` | Determinístico | O conjunto de ferramentas chamadas é exatamente o esperado |
| `tool_argument_accuracy` | Determinístico | Os argumentos passados batem com o schema/valor esperado |
| `safety` | Determinístico | Reprova qualquer *tentativa* de chamar uma ferramenta de risco alto — mesmo que o gate de aprovação (ADR-003) tenha bloqueado a execução |
| `handoff` | Determinístico | Em cenários multi-agente, se o router encaminhou para o especialista certo |
| `groundedness` | LLM-as-a-Judge | Se a resposta de um agente RAG está inteiramente fundamentada no contexto recuperado |
| `llm_judge` | LLM-as-a-Judge | Julgamento semântico de qualidade quando não há resposta objetiva comparável |
| `prompt_leak` | Determinístico | Reprova se a resposta reproduz uma fatia grande do próprio system prompt |
| `pii_leak` | Determinístico | Reprova se a resposta introduz CPF/e-mail/telefone/cartão que não veio do input do caso nem do contexto recuperado |

Multi-agente (`evaluate-multi-agent`) reusa o mesmo `AgentRunner` por trás de um roteador (LLM ou determinístico para testes) que decide qual especialista atende cada caso — sem duplicar o loop de tool-calling. `--groundedness`/`--rag` funcionam nesse modo com a mesma paridade de flags do `evaluate` single-agent.

Um `quality-gate` então aplica uma política declarativa (`quality-gates/default.json`) sobre o resumo agregado do experimento — por exemplo, `accuracy_pct >= 90`, `tool_selection_pct >= 95`, `regression_delta >= -3` — e retorna PASS/FAIL, pronto para travar um merge em CI.

## Validação real, não só teórica

O dataset MVP (`datasets/service-desk-mvp/`, 100 casos: consultas informacionais, chamadas de ferramenta, argumentos incorretos, casos que exigem aprovação, prompt injection, solicitações proibidas, casos ambíguos) foi rodado contra dois providers bem diferentes, e o resultado de cada um está documentado sem maquiagem em `docs/product/requirements.md`:

- **`--provider mock`**: 99/100 — o único caso que não passa é intencional e está documentado em `tests/unit/test_cli.py`, não é um bug escondido.
- **`--provider ollama` (qwen2.5:7b) + `--llm-judge`**: 69/100 numa primeira rodada real, contra um modelo decidindo de forma autônoma (não roteirizado como o mock). As divergências foram analisadas caso a caso — algumas eram o modelo sendo *mais cauteloso* que o script assumia, não um defeito; outras eram fragilidade conhecida de comparação exata de argumentos (já registrada como limitação em `docs/specs/evaluation-metrics/spec.md`). Um bug real do motor (o `--llm-judge` sobrescrevendo o sinal de bloqueio de aprovação com "resposta vazia") foi encontrado, corrigido em `engine/evaluators/llm_judge.py`, coberto por um teste novo (`test_llm_judge_blocked_approval.py`) e revalidado nos 4 casos afetados: 4/4.

Esse é o tipo de honestidade que o próprio motor foi desenhado para forçar: overfitar o dataset para "passar" não é avaliação — é o oposto do que o `docs/specs/multi-agent-eval/tasks.md` chama explicitamente de anti-padrão.

## Estrutura

```
AgentLab/
├── engine/              # Evaluation Engine (Python) — CLI, runner, evaluators,
│                         #   quality gates, regressão, RAG, multi-agente, persistência
├── apps/
│   ├── api/             # Fastify + TypeScript — expõe experiments/traces/evaluate via HTTP
│   └── web/             # Next.js 16 + React 19 — dashboard de resultados
├── datasets/            # Suites de evaluation cases versionadas (service-desk, RAG, safety, multi-agent)
├── agents/              # System prompts dos agentes avaliados
├── quality-gates/       # Políticas declarativas (default.json)
├── docs/
│   ├── product/         # vision.md, requirements.md — escopo e critérios de aceite por fase
│   ├── architecture/decisions/  # ADRs
│   └── specs/           # spec.md + plan.md + tasks.md + contracts/ por feature
├── tests/               # 111 testes Python (unit + integração), rodando contra Postgres real em CI
├── docker/              # Dockerfile de produção da API (Node + Python juntos)
└── .github/workflows/   # CI: pytest, vitest da API, build do dashboard, E2E do dashboard (Playwright)
```

## Stack

| Camada | Tecnologia |
|---|---|
| Evaluation Engine | Python 3.12 |
| Persistência | PostgreSQL (Neon gerenciado — ADR-005) |
| API | Fastify 5 + TypeScript |
| Dashboard | Next.js 16, React 19, Tailwind |
| Testes | pytest (unit + integração), Vitest (API), Playwright (E2E do dashboard) |
| CI/CD | GitHub Actions — Postgres real como serviço, não mockado |
| Deploy (produção, plano free) | Vercel (`apps/web`) + Render (`apps/api`, Docker) + Neon (banco) |
| Providers de LLM implementados | Mock (determinístico, scriptável via JSON) e Ollama (modelos locais, ex. `qwen2.5:7b`) |

`ProviderAdapter` é a interface abstrata que desacopla o runner do provider — um adapter para Claude/OpenAI é possível de adicionar sem tocar no núcleo, mas **hoje não está implementado**; só Mock e Ollama existem no código.

## Como rodar

```bash
# 1. Dependências do Evaluation Engine
pip install -r engine/requirements.txt

# 2. Validar um dataset
python -m engine.cli dataset validate datasets/service-desk-mvp/dataset.json

# 3. Rodar uma avaliação com o provider mock (determinístico, não precisa de LLM real)
python -m engine.cli evaluate datasets/service-desk-mvp/dataset.json \
  --provider mock --scripts datasets/service-desk-mvp/scripts.json \
  --agent service-desk --prompt-file agents/service-desk-system-prompt.txt

# 4. Rodar contra um modelo local via Ollama, com LLM-as-a-Judge
python -m engine.cli evaluate datasets/service-desk-mvp/dataset.json \
  --provider ollama --model qwen2.5:7b --llm-judge \
  --agent service-desk --prompt-file agents/service-desk-system-prompt.txt

# 5. Aplicar a política de quality gate sobre um experimento já rodado
python -m engine.cli quality-gate <experiment_id> --policy quality-gates/default.json

# 6. Avaliação multi-agente (router decide qual especialista atende cada caso)
python -m engine.cli evaluate-multi-agent datasets/multi-agent-mvp/dataset.json \
  --specialists datasets/multi-agent-mvp/specialists.json \
  --provider mock --scripts datasets/multi-agent-mvp/scripts.json \
  --router mock --router-routes datasets/multi-agent-mvp/router_routes.json
```

```bash
# Testes
python -m pytest tests/unit -v
python -m pytest tests/integration -v   # precisa de DATABASE_URL configurado

# API e dashboard
cd apps/api && npm install && npm test
cd apps/web && npm install && npm run dev

# E2E do dashboard (Playwright) — não depende de API/Postgres rodando
cd apps/web && npm run test:e2e
```

## Status

MVP → V1 → V2 (RAG/groundedness/LLM-as-a-Judge) → V3 (multi-agent evaluation, safety avançada) completos e validados contra providers reais (mock + Ollama), com CI rodando pytest + Vitest + Playwright. V4 (deployment) está no ar em produção — dashboard e API publicados no plano gratuito de cada provedor (ver link no topo). Detalhe completo de cada fase, achados reais e decisões de escopo em `CHANGELOG.md`; escopo e critério de aceite por fase em `docs/product/requirements.md`; visão de produto em `docs/product/vision.md`; plano de deployment em `docs/specs/deployment/`.

Pendências conhecidas, sem urgência: banco de produção reusa o Neon compartilhado com dev/CI (não é um branch isolado); red-teaming automatizado e ataques multi-turno de verdade continuam fora de escopo (`docs/specs/advanced-safety/spec.md`).

---

Desenvolvido por **[Vinícius Bujes de Lima](https://github.com/BujesL)**

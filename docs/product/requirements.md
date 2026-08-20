# Requirements — Fase MVP

## Escopo do MVP

Núcleo apenas: Dataset + Evaluation Case + Agent Runner + Trace + Evaluation Engine +
persistência PostgreSQL + CLI. Dashboard e API HTTP ficam para a Fase V1.

## Critérios de aceite do MVP

1. É possível cadastrar um Evaluation Case (schema validado).
2. É possível executar uma suite de casos via CLI.
3. Cada execução gera um trace (sequência de eventos).
4. Tool calls são registradas sem expor raciocínio privado do modelo.
5. Tokens, latência e custo são calculados por execução.
6. Tool Selection é avaliada deterministicamente (ferramenta esperada vs. chamada).
7. Tool Argument Accuracy é avaliada por comparação/schema.
8. Answer Accuracy é avaliada deterministicamente quando há resposta objetiva.
9. Resultados são persistidos em PostgreSQL (schema da seção "Modelo conceitual de
   dados" do documento-base).
10. Uma execução produz relatório agregado (accuracy, tool_selection, latency, cost).
11. Uma regra de quality gate consegue retornar PASS/FAIL (avaliação local, sem CI
    ainda — CI entra na Fase V1.5).
12. Testes automatizados cobrem o núcleo do Evaluation Engine (unit + integração).

## Métricas no MVP

| Métrica | Status no MVP |
|---|---|
| Answer Accuracy | Sim (determinístico) |
| Tool Selection | Sim (determinístico) |
| Tool Argument Accuracy | Sim (schema/comparação) |
| Latency | Sim |
| Token Usage | Sim |
| Cost | Sim |
| Groundedness | Fora de escopo (V2) |
| Safety | Fora de escopo (V2) |
| Regression | Fora de escopo (V1.5) |

## Fora de escopo explícito no MVP

- Dashboard web (Next.js) — Fase V1.
- API HTTP (Fastify) — Fase V1. O runner é acionado via CLI no MVP.
- Prompt Versioning formal — Fase V1.5.
- Regression Testing automatizado — Fase V1.5.
- CI/CD com GitHub Actions — Fase V1.5.
- LLM-as-a-Judge — Fase V2.
- Multi-provider (OpenAI/Gemini) — a interface Provider Adapter é definida desde o
  MVP (contrato), mas apenas o adapter Claude é implementado.

## Dataset inicial

Suite de 100 casos "Service Desk" cobrindo: consultas informacionais, chamadas de
ferramentas, argumentos incorretos, casos que exigem aprovação, prompt injection,
solicitações proibidas, casos ambíguos, casos sem dados suficientes (ver seção 24 do
documento-base). No MVP, começamos com um subconjunto reduzido (10-15 casos) para
validar o pipeline ponta a ponta antes de escalar para 100.

## Roadmap (referência)

MVP → V1 (API/dashboard) → V1.5 (prompt versioning/regression/quality gates em CI) →
V2 (Groundedness/RAG/LLM-as-Judge) → V3 (multi-agent/segurança avançada) → V4
(deployment cloud/self-hosted).

## Ideia registrada, não planejada (V3/V4 ou posterior)

**Chat na web para disparar avaliações em linguagem natural**: em vez de só
visualizar resultados já rodados, o dashboard teria uma interface de chat onde o
usuário pede em texto livre (ex.: "testa esse agente novo com o dataset de service
desk") e o sistema traduz isso numa chamada à API (`apps/api`) que dispara o
Evaluation Engine, depois resume o resultado de volta em texto.

Viável tecnicamente porque a infraestrutura já existente cobre a maior parte:
API HTTP, Evaluation Engine, conceito de Tool/Provider Adapter. Faltaria (1) um
endpoint assíncrono "rode a avaliação X" e (2) a camada de chat que interpreta o
pedido e resume a resposta.

Ressalva importante, coerente com `docs/product/vision.md` ("não usa LLM como
juiz de tudo — determinismo tem prioridade"): esse chat seria uma camada de
conveniência/UX por cima do motor determinístico, nunca um substituto das
avaliações objetivas (tool_selection, tool_argument_accuracy, etc.) por "perguntar
pra IA se passou".

Sem data nem fase definida — registrado aqui só para não perder a ideia quando o
roadmap V3/V4 for detalhado.

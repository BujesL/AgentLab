# Spec: Deployment (V4) — cloud e self-hosted

Status: **planejamento (V4) — nenhuma implementação ainda**

## Problema

Hoje o projeto só roda localmente: `engine/` via CLI direto, `apps/api` e
`apps/web` via `npm run dev`, Postgres via `docker-compose.yml` (dev) ou
Neon compartilhado (integração/CI). Não existe nenhum artefato de deploy —
sem Dockerfile para `apps/api`/`apps/web`, sem ambiente de produção
definido, sem processo de release. `docs/product/requirements.md` já lista
essa fase como "V4 (deployment cloud/self-hosted)" mas sem detalhamento
algum até este documento.

Este documento não implementa nada ainda — define o escopo e as decisões
de arquitetura para permitir quebrar o trabalho em specs/tasks concretas
depois (mesmo padrão das fases V1-V3: `spec.md` primeiro, `plan.md`/
`tasks.md` quando a direção estiver decidida).

## O que "deployment" precisa cobrir aqui

Três peças rodam separadas hoje e cada uma tem necessidades diferentes:

1. **`engine/` (Python, CLI)** — não é um serviço de longa duração; roda
   sob demanda (`agentlab evaluate ...`), tipicamente disparado por CI ou
   por um humano. Não precisa de um "deploy" no sentido de servidor
   sempre-ligado — precisa de um jeito reproduzível de rodar em qualquer
   ambiente (imagem Docker com `engine/requirements.txt` instalado é
   suficiente).
2. **`apps/api` (Node/TS)** — serviço HTTP de longa duração, serve o
   dashboard. Precisa rodar continuamente, com `DATABASE_URL` apontando
   para Postgres de produção.
3. **`apps/web` (Next.js)** — front-end, hoje `next dev`/`next start`.
   Precisa de `API_URL` apontando para a API em produção.

Banco de dados: já não é um problema novo — o projeto já usa Neon
(Postgres gerenciado) para os ambientes fora do Docker local, então
"produção" provavelmente reusa essa mesma escolha em vez de introduzir um
provedor novo.

## Duas rotas possíveis (a decidir, não decidido aqui)

### Rota A — Cloud gerenciado (menor esforço operacional)

- `apps/web` → Vercel (é Next.js; deploy nativo, zero config de servidor).
- `apps/api` → um PaaS que rode um processo Node (Fly.io, Render, Railway).
- Postgres → Neon (já em uso).
- CD: GitHub Actions dispara deploy após CI verde (`on: push: main`),
  reusando o workflow existente como gate.

### Rota B — Self-hosted (Docker Compose, servidor próprio)

- `docker-compose.yml` ganha serviços novos (`api`, `web`) ao lado do
  `postgres` que já existe — cada um com um `Dockerfile` em `docker/`.
- Precisa de um host (VM própria, ou um serviço tipo Coolify/Dokploy por
  cima de Docker) — mais controle, mais responsabilidade operacional
  (TLS, backups do Postgres, updates de SO).

Nenhuma das duas está descartada — a decisão real depende de onde isso vai
rodar de fato (uso pessoal/portfólio vs. uso por terceiros), o que ainda
não foi definido. Este spec assume que as duas rotas compartilham a mesma
pré-condição (Dockerfiles para `apps/api`/`apps/web`), então esse é o
primeiro passo concreto independente da rota escolhida.

## Dentro do escopo desta fase (quando avançar além do planejamento)

- `Dockerfile` para `apps/api` (build TS → `node dist/...`) e para
  `apps/web` (`next build` → `next start`), multi-stage para imagem final
  enxuta.
- Variáveis de ambiente de produção documentadas (`DATABASE_URL`,
  `API_URL`) — sem segredo nenhum commitado, mesmo padrão de `.env.example`
  já em uso.
- Um dos dois: `docker-compose.yml` de produção (Rota B) OU configuração de
  deploy declarativa do provedor escolhido (Rota A, ex. `fly.toml`).
- CD mínimo: workflow novo (ou extensão do `ci.yml`) que builda e publica
  as imagens/faz o deploy só depois do job de testes passar — nunca em
  paralelo, nunca se os testes falharem.

## Fora de escopo nesta fase

- Autoscaling, multi-região, CDN dedicado — este projeto não tem tráfego
  que justifique isso; infraestrutura deve ser proporcional ao uso real.
- Observability de produção (logs centralizados, métricas de
  infraestrutura, alerting) — diferente das métricas que o próprio produto
  já coleta (tokens/custo/latência de avaliação), isso seria sobre a saúde
  dos serviços em si. Registrado como possível V5, não V4.
- Autenticação/multi-tenancy no dashboard — hoje é uma ferramenta de uso
  único/interno; expor publicamente sem login é uma decisão de produto
  separada desta spec de infraestrutura.
- Migração de Neon para Postgres self-hosted — Rota B usa Docker só para
  `apps/api`/`apps/web`; o banco continua em Neon a menos que uma spec
  futura decida o contrário.

## Próximos passos concretos

1. Decidir Rota A vs. B (depende de uso pretendido — pergunta para o
   usuário, não uma decisão técnica pura).
2. `plan.md` com o desenho detalhado da rota escolhida.
3. `tasks.md` quebrando em passos executáveis (Dockerfiles primeiro, depois
   CD).

## Critérios de aceitação (desta fase de planejamento)

- [x] Três peças do sistema (`engine`, `apps/api`, `apps/web`) e suas
      necessidades de deploy diferentes estão documentadas.
- [x] Duas rotas de deployment (cloud gerenciado vs. self-hosted) estão
      descritas com trade-offs, sem escolher uma pelo usuário.
- [x] Escopo desta fase (Dockerfiles + CD mínimo) e o que fica de fora
      (autoscaling, observability de infra, auth, migração de banco) estão
      explícitos.
- [ ] Rota escolhida pelo usuário (pendente — ver "Próximos passos").

# Spec: CI/CD (GitHub Actions)

Status: **em desenvolvimento (V1.5)**

## Problema

Até aqui, toda validação (testes unitários, integração, build) foi rodada
manualmente por mim durante o desenvolvimento. O documento-base (seção 20)
prevê o fluxo `git push → Unit Tests → Integration Tests → Agent Evaluation
→ Quality Gate → PASS/FAIL`. Sem CI, nada impede um push quebrado de entrar
no repositório sem ninguém perceber.

## Resolve também o débito do ADR-006

O ADR-006 (Regression Testing) registrou como "médio prazo": usar um
Postgres isolado para testes de integração, em vez do Neon compartilhado
com dados de demonstração. O GitHub Actions resolve isso de graça — um
**service container Postgres efêmero**, que nasce e morre a cada execução
do workflow, nunca é o mesmo banco usado para demonstração local. O fix de
limpeza cirúrgica (ADR-006) continua valendo para quem rodar os testes
localmente contra o Neon, mas em CI o isolamento é total por construção.

## Resultado esperado

Um único workflow (`.github/workflows/ci.yml`) que, a cada push/PR:

1. Sobe um Postgres efêmero (service container).
2. Roda testes unitários Python (`tests/unit`).
3. Aplica o schema no Postgres efêmero.
4. Roda testes de integração Python (`tests/integration`).
5. Roda testes da API (`apps/api`, unit + integração, mesmo Postgres
   efêmero).
6. Builda o Dashboard (`apps/web` — `npm run build`, que já pega erros de
   TypeScript, mesmo sem testes automatizados de UI ainda).

## Escopo

### Dentro do escopo (V1.5)

- Um workflow, um job, execução sequencial (não precisa de matrix/paralelismo
  para o tamanho atual do projeto).
- Postgres efêmero via `services:` do GitHub Actions.
- Falha em qualquer etapa bloqueia o workflow inteiro (`fail-fast` implícito
  do bash `set -e` / exit codes).

### Fora do escopo (fases futuras)

- Deploy automático (CD de verdade) — não há ambiente de produção definido
  ainda (Fase V4, "Cloud/self-hosted deployment").
- Quality Gate como etapa obrigatória do CI (bloquear merge se
  `quality-gate` falhar) — o comando existe e funciona (spec anterior), mas
  aplicá-lo automaticamente exigiria um experimento de referência gerado
  dentro do próprio CI, o que este workflow ainda não faz (rodar
  `evaluate` end-to-end como parte do pipeline). Registrado como próximo
  passo natural, não implementado agora para não inflar o escopo desta
  spec.
- Cache de dependências (`actions/cache`) — otimização, não correção;
  pode vir depois se o tempo de CI incomodar.

## Critérios de aceitação

- [ ] Workflow dispara em push para `main` e em pull requests.
- [ ] Testes unitários Python rodam sem depender do Postgres.
- [ ] Testes de integração Python rodam contra o Postgres efêmero do CI,
      não contra o Neon de desenvolvimento.
- [ ] Testes da API rodam contra o mesmo Postgres efêmero.
- [ ] Build do Dashboard roda e falha se houver erro de TypeScript.
- [ ] Um push com um teste quebrado faz o workflow falhar (vermelho no
      GitHub) — validado rodando de verdade, não só lendo o YAML.

# Spec: API (Fastify + TypeScript)

Status: **em desenvolvimento (V1)**

## Problema

Tudo hoje só é acessível via CLI Python. O Dashboard (Next.js, spec já
existente em `docs/specs/web-dashboard/`) precisa de uma API HTTP para ler
experimentos, traces e resultados — e não pode importar o Evaluation Engine
Python diretamente (ADR-001: Engine independente da interface web).

## Como a API se relaciona com o Evaluation Engine (decisão de arquitetura)

Duas formas de comunicação, sem nunca importar código Python dentro do Node:

1. **Leitura**: a API lê diretamente do PostgreSQL (mesmo banco que o Engine
   escreve) usando `pg` (node-postgres), sem ORM — mesma filosofia de
   `engine/persistence/repository.py` (SQL explícito, sem acoplamento a
   framework). API e Engine são dois clientes independentes do mesmo banco.
2. **Escrita/execução**: a API aciona uma avaliação chamando o CLI Python via
   subprocess (`python -m engine.cli evaluate ...`), nunca reimplementando a
   lógica de avaliação em TypeScript. Reforça ADR-001.

## Resultado esperado

Endpoints mínimos para o Dashboard (Fase V1) consumir:

- `GET /health` — liveness check.
- `GET /experiments` — lista experimentos.
- `GET /experiments/:id/summary` — accuracy/latência/custo agregados
  (mesma lógica de `engine/experiments/summary.py`, reimplementada em SQL
  do lado do Node — ver "Escopo" abaixo sobre por que não é duplicação
  problemática).
- `GET /traces/:id` — trace completo com eventos, para o Trace Viewer.
- `POST /evaluate` — dispara uma avaliação via subprocess do CLI Python,
  retorna o resultado.

## Escopo

### Dentro do escopo (V1)

- Os 5 endpoints acima.
- Conexão ao Postgres via `DATABASE_URL` (mesma variável de ambiente do
  Engine — uma fonte de verdade para a connection string).
- Testes usando `fastify.inject()` (sem precisar subir servidor de verdade)
  para rotas simples, e testes de integração reais contra o Neon para as
  que tocam banco (mesmo padrão do lado Python).

### Nota sobre duplicação de lógica de agregação

`GET /experiments/:id/summary` reimplementa a mesma consulta SQL de
`summarize_experiment` (Python) em TypeScript. Isso é uma duplicação
deliberada, não um descuido: a alternativa seria a API chamar um subprocess
Python para cada leitura de summary, o que é lento e desnecessário para uma
operação de leitura pura. Se essa duplicação virar fonte de bugs (os dois
lados divergindo), a spec futura de "API v2" pode extrair a query para um
lugar único (ex. view SQL materializada) — registrado aqui como débito
técnico consciente, não escondido.

### Fora do escopo (fases futuras)

- Autenticação/autorização — MVP/V1 é uso local/interno, sem exposição
  pública. V2+ se o produto for multi-usuário.
- `POST /evaluate` assíncrono com fila de jobs — V1 roda síncrono (aceitável
  para datasets pequenos como o MVP de 12 casos); filas ficam para quando
  datasets forem maiores (100+ casos, seção 24).
- Paginação em `GET /experiments` — adiada até existir volume que justifique.

## Critérios de aceitação

- [ ] `GET /health` retorna 200 com `{"status": "ok"}`.
- [ ] `GET /experiments` retorna array de experimentos (vazio se não houver).
- [ ] `GET /experiments/:id/summary` retorna os mesmos números que
      `summarize_experiment` (Python) para o mesmo experimento — validado
      comparando as duas saídas para um experimento real.
- [ ] `GET /traces/:id` retorna 404 estruturado (não crash) para id
      inexistente.
- [ ] `GET /traces/:id` retorna eventos na ordem correta por `sequence`.
- [ ] `POST /evaluate` aciona o CLI e retorna exit code + saída resumida.

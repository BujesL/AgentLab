# Plan: API (Fastify + TypeScript)

## Stack

- Fastify 4 + TypeScript (ADR-002).
- `pg` (node-postgres) para conexão direta ao Postgres, sem ORM.
- `vitest` para testes (stack já prevista na seção 8 do documento-base).
- `tsx` para rodar TypeScript em dev sem build step separado.

## Estrutura

```
apps/api/
├── package.json
├── tsconfig.json
├── src/
│   ├── server.ts        # cria e exporta o Fastify app (para testes com inject)
│   ├── index.ts         # entrypoint: server.listen()
│   ├── db.ts            # Pool de conexão (lê DATABASE_URL)
│   └── routes/
│       ├── health.ts
│       ├── experiments.ts
│       ├── traces.ts
│       └── evaluate.ts
└── tests/
    ├── health.test.ts        # fastify.inject, sem banco
    └── experiments.test.ts   # integração real contra Neon (skip sem DATABASE_URL)
```

## `src/db.ts`

```ts
import { Pool } from "pg";

export function createPool(): Pool {
  const connectionString = process.env.DATABASE_URL;
  if (!connectionString) {
    throw new Error("DATABASE_URL não definida");
  }
  return new Pool({ connectionString });
}
```

## Rotas

`GET /health` → `{ status: "ok" }`, sem tocar banco.

`GET /experiments` → `SELECT id, agent_version_id, dataset_id, model, status FROM experiment ORDER BY id`.

`GET /experiments/:id/summary` → mesma query SQL de
`engine/experiments/summary.py::summarize_experiment`, portada para
TypeScript (ver nota de duplicação deliberada em spec.md).

`GET /traces/:id` → busca `trace` + `trace_event` ordenado por `sequence`,
monta JSON no mesmo formato do contrato `docs/specs/traces/contracts/trace.schema.json`.
404 com `{ error: "trace not found" }` se ausente.

`POST /evaluate` → `body: { datasetPath, scriptsPath, agent?, agentVersion?, model? }`.
Executa via `child_process.spawn("python", ["-m", "engine.cli", "evaluate", ...])`
a partir do `cwd` do repo (`agent-evaluation-lab/`), captura stdout/stderr e
exit code, retorna `{ exitCode, output }`. Timeout razoável (ex. 60s) para não
travar a API se o subprocess pendurar.

## Passos de implementação

1. `apps/api/package.json` + `tsconfig.json`.
2. `npm install` (fastify, pg, tsx, vitest, typescript, @types/node, @types/pg).
3. `src/db.ts`, `src/server.ts`, `src/index.ts`.
4. `src/routes/{health,experiments,traces,evaluate}.ts`.
5. `tests/health.test.ts` (sem banco).
6. `tests/experiments.test.ts`, `tests/traces.test.ts` (integração real,
   skip sem `DATABASE_URL`, mesmo padrão dos testes Python).
7. Rodar `npm test`, confirmar passagem real.
8. Comparar `GET /experiments/:id/summary` com `summarize_experiment`
   (Python) para o mesmo experiment_id real criado na spec anterior —
   evidência de que os dois lados concordam.

## Fora deste plano

Autenticação, filas assíncronas, paginação — ver "fora do escopo" em spec.md.

# Tasks: API

- [x] T1 — spec.md com critérios de aceitação e nota sobre duplicação deliberada.
- [x] T2 — plan.md com estrutura e stack.
- [x] T3 — `apps/api/package.json` + `tsconfig.json`, `npm install`.
      Nota: `fastify@4.x`/`vitest@2.x` iniciais tinham 7 vulnerabilidades
      conhecidas (3 moderate, 3 high, 1 critical — DoS, bypass de validação).
      Atualizado para `fastify@^5.12.1` e `vitest@^4.1.11` antes de escrever
      qualquer rota, `npm audit` limpo depois da troca.
- [x] T4 — `src/db.ts`, `src/server.ts`, `src/index.ts`.
- [x] T5 — Rotas: health, experiments, traces, evaluate.
- [x] T6 — `tests/health.test.ts`.
- [x] T7 — `tests/experiments.test.ts`, `tests/traces.test.ts`.
- [x] T8 — Rodar `npm test`, confirmar passagem real.
      Evidência (2026-08-19): sem `DATABASE_URL` → `1 passed | 5 skipped`
      (health roda, resto pula corretamente). Com `DATABASE_URL` (Neon
      real) → `Test Files 3 passed (3)`, `Tests 6 passed (6)`.
- [x] T9 — Comparar `/experiments/:id/summary` com `summarize_experiment`
      Python para o mesmo experimento real (`8849dcea-5329-4960-ab02-2c350d299560`,
      criado na spec de Experiment Manager).
      Evidência: API retornou
      `{"total_cases":12,"passed":11,"accuracy_pct":91.66666666666666,"avg_latency_ms":0.051856040954589844,"avg_cost":0}`
      — idêntico ao resultado do `summarize_experiment` Python registrado em
      `docs/specs/experiments/tasks.md`.
- [x] T10 — Revisar diff contra spec.md:
      - `GET /health` 200 + `{"status":"ok"}`: `tests/health.test.ts`.
      - `GET /experiments` retorna array: `tests/experiments.test.ts`.
      - `/summary` bate com o Python: evidência do T9 acima.
      - `GET /traces/:id` 404 estruturado para id inexistente:
        `tests/traces.test.ts` (`returns 404 for an unknown trace id`).
      - Eventos em ordem por sequence: `tests/traces.test.ts`
        (`returns events in sequence order`, inserido fora de ordem no banco
        de propósito para provar o `ORDER BY sequence ASC`).
      - `POST /evaluate` aciona CLI via subprocess e retorna exitCode +
        output: implementado em `src/routes/evaluate.ts` (sem teste
        automatizado dedicado — chamar um subprocess Python de dentro do
        Vitest é frágil/lento para rodar em toda suíte; validação manual
        fica registrada como item aberto, ver observação abaixo).

## Observação: cobertura incompleta em POST /evaluate

`POST /evaluate` não tem teste automatizado (unit nem integração) — só as
outras 4 rotas foram verificadas com evidência de teste real. Isso é uma
lacuna conhecida, não escondida: subprocess spawning de Python dentro de
testes Vitest é viável mas mais lento/frágil (depende do `.venv` estar no
PATH do processo de teste). Fica como débito técnico registrado para quando
a rota for exercitada pelo Dashboard (Fase V1, próxima sub-etapa) — nesse
ponto testamos via uso real, e se precisar de teste automatizado formal,
volta aqui.

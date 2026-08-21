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

## T11 — Estender /experiments/:id/summary com métricas do V2 (2026-08-21)

Confirmado que o V1 (API+Dashboard) e o V1.5 (Quality Gates/Prompt
Versioning/Regression/CI) já estavam completos desde 2026-08-19 — antes das
sessões de V2 (LLM-as-a-Judge/Groundedness/RAG). O Dashboard só mostrava
`accuracy_pct` (agregado por AND de todos os avaliadores), sem visibilidade
individual das métricas novas.

**Mudança**: `GET /experiments/:id/summary` ganha `metric_scores: {metric,
pct}[]`, calculado genericamente via `jsonb_each_text(scores)` sobre todos os
`evaluation_result` do experimento — nenhuma métrica é hardcoded, então
qualquer avaliador futuro (`scores` com uma chave nova) aparece
automaticamente sem mudança de API.

- `apps/api/src/routes/experiments.ts`: query adicional agregando por
  `kv.key`.
- `apps/web/lib/api.ts`: `ExperimentSummary.metric_scores`.
- `apps/web/app/dashboard/page.tsx`: cards agregados "LLM Judge"/
  "Groundedness" (só aparecem quando ao menos um experimento reportou a
  métrica) + badges por linha de experimento.
- `apps/web/app/compare/page.tsx`: linhas de métrica dinâmicas — união das
  chaves de `metric_scores` de A e B, não uma lista fixa.

**Bug real encontrado durante a verificação manual (não de código, de
processo de dev)**: `npm run dev` do `apps/api` não usa `--watch`; um
processo antigo (código anterior à mudança) continuava vivo na porta 3001
depois de reiniciar o servidor com `&`, porque `npm run dev &` só mata o
wrapper `npm`, não o processo `node` filho — o novo processo falhava em
silêncio com `EADDRINUSE` no log, e as requisições continuavam sendo
servidas pelo processo velho sem `metric_scores`. Diagnosticado lendo o log
do servidor, corrigido matando o processo pela porta (`Get-NetTCPConnection
-LocalPort 3001 | Stop-Process`) antes de reiniciar.

**Validado com dado real**: persistido um experiment real (`agentlab
evaluate datasets/rag-groundedness-mvp/dataset.json --agent
rag-groundedness --llm-judge --groundedness`, sem `--no-persist`),
confirmado no dashboard e no `/compare` mostrando `LLM Judge: 100.0%` e
`Groundedness: 100.0%` para esse experimento, e `groundedness` ausente (não
zero, ausente) nos experimentos antigos que nunca rodaram com essa flag —
comportamento correto do "average only over experiments that reported it".

Testes: `apps/api/tests/experiments.test.ts` ganhou um teste cobrindo
`metric_scores` com múltiplas chaves (7/7 passing). `npm run build` do
`apps/web` limpo (TypeScript confere os novos tipos). Suíte Python
inalterada (75 passed + 20 skipped — este incremento não tocou o Engine
Python).

## Observação: cobertura incompleta em POST /evaluate

`POST /evaluate` não tem teste automatizado (unit nem integração) — só as
outras 4 rotas foram verificadas com evidência de teste real. Isso é uma
lacuna conhecida, não escondida: subprocess spawning de Python dentro de
testes Vitest é viável mas mais lento/frágil (depende do `.venv` estar no
PATH do processo de teste). Fica como débito técnico registrado para quando
a rota for exercitada pelo Dashboard (Fase V1, próxima sub-etapa) — nesse
ponto testamos via uso real, e se precisar de teste automatizado formal,
volta aqui.

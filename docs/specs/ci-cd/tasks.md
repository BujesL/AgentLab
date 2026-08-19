# Tasks: CI/CD

- [x] T1 — spec.md com critérios de aceitação.
- [x] T2 — plan.md.
- [x] T3 — `.github/workflows/ci.yml`.
      Correção real durante a implementação: o workflow inicial usava
      `working-directory: agent-evaluation-lab` (copiado do plano
      pensando em monorepo aninhado), mas o repositório Git raiz **já é**
      o conteúdo de `agent-evaluation-lab/` (confirmado via
      `gh api repos/BujesL/AgentLab/contents`) — corrigido antes do
      primeiro push, senão o checkout nunca encontraria os arquivos.
- [x] T4 — Push e observar execução real via `gh run watch`.
      Evidência (2026-08-19, run `32263833130`): todas as etapas ✓ em
      1m6s — `Run Python unit tests`, `Apply database schema`,
      `Run Python integration tests` (Postgres efêmero do CI, não o Neon),
      `Install and test API`, `Install and build Web dashboard`.
- [x] T5 — Teste negativo: falha deliberada, confirmar vermelho, reverter.
      Evidência: commit `9cc4bb7` (teste `assert False` deliberado) → run
      `32263993228` → **`X Run Python unit tests`**, workflow parou ali
      (steps seguintes marcados `-`, não rodaram) — confirma que o CI
      bloqueia de verdade, não é decorativo. Revertido no commit `fb25925`
      → run `32264098246` → verde de novo, `✓` em todas as etapas.
- [x] T6 — Revisar diff contra spec.md:
      - Dispara em push para `main`: `on: push: branches: [main]` +
        evidência de 3 execuções reais acionadas por push.
      - Testes unitários Python sem depender do Postgres: rodam antes do
        `Apply database schema` no workflow (ordem confirmada no log).
      - Testes de integração contra Postgres efêmero do CI: `services:
        postgres` no job, não referencia `DATABASE_URL` do Neon em
        nenhum lugar do workflow.
      - Testes da API contra o mesmo Postgres efêmero: mesma `env:
        DATABASE_URL` do job, confirmado no log (`Install and test API`
        passou, o que exige DB — os testes de integração da API não são
        skipados).
      - Build do Dashboard falha em erro de TypeScript: já validado
        indiretamente (o erro real de `experiments: any[]` — spec de
        web-dashboard — teria quebrado este mesmo step se reintroduzido).
      - Push com teste quebrado faz o workflow falhar: evidência do T5.

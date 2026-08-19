# Plan: Dashboard (Next.js) — implementação V1

Complementa `spec.md` (decisão de design já registrada antes do MVP). Este
plano cobre a implementação real, feita na fase V1 depois da API existir.

## Stack

Next.js 15 (App Router) + React 19 + TypeScript + Tailwind, scaffolded
manualmente (sem `create-next-app`/`shadcn init` interativos, que bloqueariam
em prompts) — mesma estrutura de arquivos que os dois geradores produziriam
(`app/`, `lib/utils.ts` com `cn()`, `tailwind.config.ts`, alias `@/*`).

## Duas telas, por decisão já registrada em spec.md

- `app/page.tsx` (`/`) — landing com `KineticGrid`, hero + CTA. Decorativo,
  sem dados reais.
- `app/dashboard/page.tsx` (`/dashboard`) — tela densa de dados (seção 25),
  **sem** `KineticGrid` (canvas + rAF é caro e desnecessário aqui, conforme
  já registrado em spec.md).

## Integração com a API

`lib/api.ts` — `fetchExperiments()`, `fetchExperimentSummary(id)`, client
`fetch` simples contra `API_URL` (env var, default `http://localhost:3001`).
`app/dashboard/page.tsx` é um Server Component (`force-dynamic`, sem cache)
que busca a lista de experimentos e, para cada um, seu summary — renderiza
os cards agregados (Experiments/Evaluations/Accuracy/Avg Cost/Avg Latency,
seção 25) e a lista "Recent Experiments" com PASS/FAIL.

Falha de conexão com a API não quebra a página — mostra uma mensagem de
erro inline (princípio "falhar explicitamente", mas sem derrubar a UI
inteira por uma dependência externa fora do ar).

## Passos de implementação

1. Scaffold manual: `package.json`, `tsconfig.json`, `next.config.mjs`,
   `tailwind.config.ts`, `postcss.config.mjs`, `lib/utils.ts`.
2. `app/layout.tsx`, `app/globals.css`.
3. `app/page.tsx` (landing com KineticGrid, já usando o componente salvo
   anteriormente).
4. `lib/api.ts`, `app/dashboard/page.tsx`.
5. `npm install`.
6. `npm run build` (verifica erros de TypeScript/compilação reais).
7. Subir API real (Neon) + `npm run dev`, testar `/dashboard` de verdade no
   navegador ou via `curl`/fetch do HTML renderizado, confirmar que os
   números batem com a API.

## Fora deste plano

Trace Viewer visual (tela de detalhe de um trace) — não pedido ainda,
adiado para quando for necessário. Autenticação — fora de escopo (ver
`docs/specs/api/spec.md`).

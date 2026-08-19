# Tasks: Dashboard (Next.js) — implementação V1

- [x] T1 — Componente `KineticGrid` salvo (já feito antes do MVP).
- [x] T2 — plan.md com decisões de implementação.
- [x] T3 — Scaffold manual (package.json, tsconfig, next/tailwind/postcss config).
- [x] T4 — `lib/utils.ts`, `app/layout.tsx`, `app/globals.css`.
- [x] T5 — `app/page.tsx` (landing com KineticGrid).
- [x] T6 — `lib/api.ts`, `app/dashboard/page.tsx`.
- [x] T7 — `npm install`.
      Nota: `next@15.0.0` inicial trazia 3 vulnerabilidades altas (postcss
      XSS/path traversal, sharp/libvips CVEs) via dependências internas.
      Atualizado para `next@^16.3.1` antes de prosseguir — `npm audit`
      limpo (`found 0 vulnerabilities`).
- [x] T8 — `npm run build`, confirmar sem erros de TypeScript.
      Achado real: `experiments` sem tipo explícito quebrava o build
      (`TS7034`/`TS7005`, implicit any). Corrigido com
      `let experiments: Experiment[]`. Rebuild limpo:
      `✓ Compiled successfully`, `✓ Finished TypeScript`.
- [x] T9 — Rodar API real (Neon, porta 3101) + `npm run dev` (porta 3200),
      testar `/dashboard` de verdade.
      Evidência (2026-08-19): HTML renderizado continha `30.6%` (accuracy
      média de 3 experimentos reais), `91.7%` (o experimento MVP da spec de
      Experiment Manager) e os cards PASS/FAIL — dados vieram da API/Neon
      de verdade, não mockados.
      Achado real (documentado, não corrigido agora): o PASS/FAIL na UI usa
      limiar de `accuracy_pct === 100`, então o experimento com 91.7% (que
      é um resultado razoável) aparece como FAIL. É um limiar simplista —
      um quality gate de verdade (seção 20 do documento-base) usa algo como
      `accuracy >= 90%` configurável, não igualdade a 100%. Fica registrado
      como item para a spec de Quality Gates (Fase V1.5), que é quem deve
      formalizar esse limiar — a UI hoje só reflete um placeholder.
      Efeito colateral encontrado: Next.js 16 gera automaticamente
      `AGENTS.md`/`CLAUDE.md` no projeto (`agentRules`, ligado por padrão).
      Desabilitado via `agentRules: false` em `next.config.mjs` e os
      arquivos gerados foram removidos — não fazem parte da documentação
      real do projeto.
- [x] T10 — Revisar diff contra spec.md:
      - Fundo `KineticGrid` só na landing (`/`): `app/page.tsx`.
      - Tela de dados densa sem `KineticGrid`: `app/dashboard/page.tsx`.
      - Dados reais da API renderizados: evidência do T9 acima.
      - Falha de API não derruba a página: `try/catch` em
        `DashboardPage` + mensagem inline (não testado automaticamente,
        só por inspeção de código — ver observação abaixo).

## Observações / débito técnico registrado

- Limiar PASS/FAIL de 100% é placeholder — corrigir quando a spec de
  Quality Gates existir.
- Sem testes automatizados para o Dashboard (nem unitários nem E2E) — a
  validação foi feita rodando de verdade (API + browser/curl) porque
  Next.js/React Testing Library não estavam no escopo desta rodada. Se o
  Dashboard crescer além dessas duas telas, vale adicionar Vitest +
  Testing Library aqui, mesma decisão de stack já usada na API.

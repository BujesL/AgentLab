# Spec: Tela principal do dashboard (`apps/web`)

Status: **planejado para Fase V1** (dashboard só entra em escopo depois do MVP —
ver `docs/product/requirements.md`). Este documento registra a decisão de design
da tela principal antes da implementação, conforme metodologia Spec-Driven.

## Requisito

A tela principal (landing/hero do dashboard) deve usar o componente `KineticGrid`
como fundo interativo, com o conteúdo real do dashboard (visão geral de
experiments/evaluations, seção 25 do documento-base) sobreposto no `children`.

## Componente de origem

Componente de terceiro (`kinetic-grid.tsx` + demo) fornecido pelo usuário em
2026-08-18. Já copiado para `apps/web/components/ui/`:

- `apps/web/components/ui/kinetic-grid.tsx` — componente principal.
- `apps/web/components/ui/kinetic-grid.demo.tsx` — exemplo de uso (referência,
  não é a tela final — o conteúdo real do dashboard substituirá o hero de demo).

## Pré-requisitos de projeto (a validar quando `apps/web` for criado)

`apps/web` ainda **não existe** como projeto Next.js (essa pasta só tinha o
placeholder de estrutura). Antes de este componente rodar de verdade, a Fase V1
precisa:

1. **Scaffold do Next.js com TypeScript**: `npx create-next-app@latest apps/web --typescript`
   (ou configuração manual dentro da estrutura já existente do monorepo).
2. **Tailwind CSS**: incluso por padrão no scaffold do Next.js recente; se ausente,
   `npx shadcn@latest init` cuida de configurar Tailwind + `tailwind.config` +
   `globals.css` automaticamente.
3. **shadcn CLI**: rodar `npx shadcn@latest init` para gerar a estrutura padrão
   (`components.json`, `lib/utils.ts` com a função `cn()`, alias `@/*`).
   - Caminho default de componentes do shadcn é `components/ui/` — **é importante
     manter esse caminho** porque (a) os geradores do shadcn e outros componentes
     de terceiro assumem esse import (`@/components/ui/...`), (b) mantém
     consistência entre componentes gerados pela CLI e componentes copiados
     manualmente como este, (c) evita imports quebrados ao rodar
     `npx shadcn add <outro-componente>` no futuro.
   - Neste repositório o caminho já usado é `apps/web/components/ui/`, compatível.
4. **`lib/utils.ts`** com a função `cn` (merge de classes clsx + tailwind-merge) —
   é a dependência direta do componente (`import { cn } from "@/lib/utils"`).
   Criar em `apps/web/lib/utils.ts`:
   ```ts
   import { clsx, type ClassValue } from "clsx";
   import { twMerge } from "tailwind-merge";

   export function cn(...inputs: ClassValue[]) {
     return twMerge(clsx(inputs));
   }
   ```

## Dependências externas (npm) a instalar quando `apps/web` existir

| Pacote | Motivo |
|---|---|
| `next`, `react`, `react-dom` | Framework base |
| `typescript`, `@types/react`, `@types/node` | TypeScript |
| `tailwindcss`, `postcss`, `autoprefixer` | Estilos (ou via shadcn init) |
| `clsx`, `tailwind-merge` | Função `cn()` usada pelo componente |
| `lucide-react` | Ícones — o dashboard real (seção 25 do doc-base) provavelmente precisará de ícones para métricas/status, mesmo que o `kinetic-grid.tsx` em si não use nenhum |

Não há assets de imagem exigidos por este componente (é 100% canvas/JS). Não é
necessário Unsplash aqui.

## Comportamento e responsividade

- Fundo cobre `100vw x 100vh` via `<canvas>` fixo (`position: fixed inset-0`),
  recalculado em `resize`.
- Grid reage ao mouse (warp) e a cliques (ripple) — comportamento decorativo,
  não interfere em interações do conteúdo real (`pointer-events-none` no canvas).
- Em mobile (sem mouse), o efeito de warp por proximidade do cursor não ativa;
  ripple por clique/touch deve funcionar via evento `click` (já cobre touch em
  navegadores mobile). Nenhum ajuste adicional necessário para o MVP visual.
- Duas variantes de cor: `default` (azul) e `monochrome` (preto/branco). A
  decisão de qual usar na tela principal do dashboard fica para quando a
  identidade visual do produto for definida (Fase V1) — usar `default` como
  fallback.

## Onde este componente entra no dashboard real

A tela principal (`/` do `apps/web`) usará `KineticGrid` como wrapper de layout,
substituindo o conteúdo de exemplo do `demo.tsx` pelo hero real do produto:
nome do projeto, tagline ("plataforma de avaliação reproduzível de agentes de
IA"), e CTA para acessar experiments/dashboard (seção 25 do documento-base:
Experiments, Evaluations, Accuracy, Avg Cost, Avg Latency, Recent Experiments).
O conteúdo interno das telas subsequentes (lista de experiments, trace viewer)
não deve usar `KineticGrid` — é caro (canvas + rAF) e desnecessário para telas
de dados densos; fica restrito à tela principal/landing.

## Questões em aberto (a decidir no início da Fase V1, não agora)

- Dados/props reais da tela principal: virão da API (`apps/api`) via fetch
  server-side (Next.js) — depende da API existir (item posterior no roadmap V1).
- Sem necessidade de state management global (Redux/Zustand) só para esta tela;
  local state do Next.js resolve.

## Não-ação agora

Não vamos rodar `create-next-app` nem instalar dependências agora — isso seria
antecipar a Fase V1 antes do núcleo (MVP) estar pronto, contrariando a ordem
recomendada (seção 30 do documento-base) e o ADR-002. Este documento existe só
para não perder a decisão de design e o componente fornecido.

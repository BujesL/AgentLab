# Plan: Deployment V4 — Rota A (cloud gerenciado)

Decisão registrada em `spec.md`: Vercel (`apps/web`) + PaaS Node
(`apps/api`) + Neon (banco, já em uso hoje para integração/CI).

## Achado que muda o desenho: `apps/api` não é Node puro

`apps/api/src/routes/evaluate.ts` faz
`spawn("python", ["-m", "engine.cli", "evaluate", ...], { cwd: repoRoot })`
— a rota `/evaluate` dispara o CLI Python do `engine/` como subprocesso.
Um buildpack Node genérico (Render "Web Service" padrão, Fly com detecção
automática) não inclui Python nem `engine/requirements.txt` instalados, e
essa rota quebraria silenciosamente em produção (spawn falha por `python`
não encontrado).

Consequência: `apps/api` precisa de uma imagem Docker própria com **Node +
Python 3.12** e o repo inteiro disponível (não só `apps/api/`), porque
`repoRoot` (`apps/api/src/index.ts:7`) resolve caminhos relativos ao
monorepo. Isso descarta "buildpack automático" para a API — precisa de
`docker/api.Dockerfile` e um provedor que aceite Dockerfile custom (Fly.io
e Render Docker Web Service os dois servem).

## Peça 1 — `apps/web` → Vercel

- Build nativo do Next.js, sem Dockerfile necessário.
- Variável de ambiente: `API_URL` apontando para a URL pública da API em
  produção (hoje só existe `process.env.API_URL ?? "http://localhost:3001"`
  no dashboard — nenhuma mudança de código necessária, só configurar a env
  var no projeto Vercel).
- Root directory do projeto Vercel: `apps/web` (monorepo — Vercel suporta
  isso nativamente via "Root Directory" na configuração do projeto).

## Peça 2 — `apps/api` → Fly.io (ou Render Docker Web Service)

- `docker/api.Dockerfile`: imagem base Node, instala Python 3.12 +
  `engine/requirements.txt`, copia o repo inteiro (não só `apps/api`),
  `npm ci` dentro de `apps/api`, expõe `PORT` (já lido de
  `process.env.PORT` em `src/index.ts:12`, nenhuma mudança de código
  necessária).
- Variável de ambiente: `DATABASE_URL` apontando para o Neon de produção
  (não reusar a connection string de dev/CI).
- Fly.io escolhido sobre Render nesta primeira passada só por ter
  `fly.toml` mais simples para um serviço único — sem preferência forte,
  Render Docker Web Service é equivalente se o usuário já tiver conta lá.

## Peça 3 — Neon (banco)

- Já em uso — só precisa de um branch/database de produção separado do
  usado em CI (`agentlab_ci`) e do usado em dev local
  (`agentlab_dev_only`), para não misturar dados de teste com produção.
- Nenhuma mudança de schema: `apply_schema` já é idempotente (usado hoje
  tanto em CI quanto localmente).

## CD — quando acontece o deploy

- Vercel: deploy automático já é o comportamento padrão ao conectar o repo
  GitHub (preview deploy por PR, produção no merge em `main`) — não
  precisa de step novo no `ci.yml`.
- Fly.io: `fly deploy` como step novo em `.github/workflows/ci.yml`,
  **depois** do job de testes passar (nunca em paralelo) — mesmo princípio
  do CI atual (falha em qualquer etapa anterior bloqueia o deploy).
  Precisa de `FLY_API_TOKEN` como GitHub secret.

## Feito nesta sessão (etapa 1 do plano)

- `apps/api/package.json`: scripts `build` (`tsc -p tsconfig.build.json`) e
  `start` (`node dist/index.js`) novos — não existiam, `dev` sempre rodou
  via `tsx` direto no TS fonte.
- `apps/api/tsconfig.build.json`: config de build separada da de
  desenvolvimento/typecheck (`tsconfig.json`, que inclui `tests` para o
  editor/typecheck). Sem isso, `tsc -p tsconfig.json` compilava `tests/`
  para `dist/tests/*.test.js` e o `vitest run` passava a descobrir e rodar
  os testes duas vezes (fonte + compilado) — achado real ao testar o build
  localmente, corrigido restringindo o build a `include: ["src"]`.
- `docker/api.Dockerfile`: imagem Node 20 + Python 3.12 (via venv) +
  `engine/requirements.txt`, copia o repo inteiro (contexto de build tem
  que ser a raiz do repo, não `apps/api/`), builda a API e roda
  `node apps/api/dist/index.js`. **Não testado com `docker build` de
  verdade** — Docker não está disponível neste ambiente; validar no
  primeiro `fly deploy` manual (passo 4 abaixo).
- Build/start verificados localmente sem Docker: `npm run build` +
  `node dist/index.js` sobe e escuta na porta esperada.

## Ordem de execução recomendada

1. `docker/api.Dockerfile` (pode ser escrito e testado localmente já,
   sem nenhuma conta nova).
2. Criar o projeto Vercel apontando para `apps/web` (precisa da conta do
   usuário — no MCP do Vercel já conectado a esta sessão).
3. Criar branch de produção no Neon.
4. Criar app no Fly.io, configurar `DATABASE_URL` como secret, primeiro
   deploy manual (`fly deploy`) para validar a imagem antes de automatizar.
5. Automatizar (2)-(4) no CD só depois do primeiro deploy manual funcionar
   — não vale a pena depurar CD e Dockerfile ao mesmo tempo.

## Fora desta etapa

- `docker-compose.yml` de produção (isso seria Rota B) — não se aplica
  aqui.
- Qualquer coisa da lista "Fora de escopo" do `spec.md` (autoscaling,
  observability de infra, auth, migração de banco).

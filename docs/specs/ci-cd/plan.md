# Plan: CI/CD (GitHub Actions)

## Estrutura do workflow

`.github/workflows/ci.yml`, um job (`test`), rodando em `ubuntu-latest`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env:
      POSTGRES_USER: agentlab
      POSTGRES_PASSWORD: agentlab_ci
      POSTGRES_DB: agentlab
    ports: ["5432:5432"]
    options: >-
      --health-cmd pg_isready
      --health-interval 5s
      --health-timeout 5s
      --health-retries 10

env:
  DATABASE_URL: postgresql://agentlab:agentlab_ci@localhost:5432/agentlab

steps:
  - checkout
  - setup-python (3.12)
  - pip install -r engine/requirements.txt
  - pytest tests/unit -v
  - apply schema (python -c "from engine.persistence.repository import ...")
  - pytest tests/integration -v
  - setup-node (20)
  - cd apps/api && npm ci && npm test
  - cd apps/web && npm ci && npm run build
```

## Por que um job só, sequencial

O projeto é pequeno o suficiente (MVP + V1 + parte da V1.5) para não
justificar paralelismo de jobs agora — adicionar matrix/jobs paralelos é
uma otimização de velocidade, não uma correção funcional. Documentado como
"fora do escopo" a otimização de cache/paralelismo.

## Passos de implementação

1. `.github/workflows/ci.yml`.
2. Push para o GitHub (já temos remoto configurado).
3. Observar a execução real via `gh run watch` — evidência de que o
   workflow roda e passa de verdade, não só que o YAML está sintaticamente
   correto.
4. Teste negativo: introduzir uma falha deliberada (ex. um teste que sempre
   falha), commitar, confirmar que o CI fica vermelho, reverter.

## Fora deste plano

Deploy/CD real, Quality Gate como gate obrigatório do CI, cache de
dependências — ver "fora do escopo" em spec.md.

# Plan: Persistência PostgreSQL

## Ferramenta de acesso ao banco

`psycopg` (v3, `psycopg[binary]`) puro, sem ORM — o Evaluation Engine deve
continuar leve e não acoplado a um framework (ADR-001). SQL explícito em
`schema.sql`, sem migrations tool (Alembic etc.) no MVP — schema pequeno o
suficiente para gerenciar manualmente; revisitar se crescer.

## docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: agentlab
      POSTGRES_PASSWORD: agentlab_dev_only
      POSTGRES_DB: agentlab
    ports:
      - "5432:5432"
    volumes:
      - agentlab_pgdata:/var/lib/postgresql/data
volumes:
  agentlab_pgdata:
```

Senha de desenvolvimento local, não usada em produção — mesmo assim vai para
`.env.example` (não `.env` real) para deixar claro que é só placeholder local.

## Schema (`engine/persistence/schema.sql`)

```sql
CREATE TABLE IF NOT EXISTS dataset (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS trace (
    id UUID PRIMARY KEY,
    experiment_id TEXT,
    case_id TEXT NOT NULL,
    started_at DOUBLE PRECISION NOT NULL,
    duration_ms DOUBLE PRECISION NOT NULL,
    token_usage INTEGER,
    cost DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS trace_event (
    id SERIAL PRIMARY KEY,
    trace_id UUID NOT NULL REFERENCES trace(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    type TEXT NOT NULL,
    payload JSONB NOT NULL,
    timestamp DOUBLE PRECISION NOT NULL,
    UNIQUE (trace_id, sequence)
);

CREATE TABLE IF NOT EXISTS evaluation_result (
    id SERIAL PRIMARY KEY,
    case_id TEXT NOT NULL,
    trace_id UUID REFERENCES trace(id) ON DELETE SET NULL,
    scores JSONB NOT NULL,
    passed BOOLEAN NOT NULL,
    failure_reason TEXT
);
```

`trace_id` em `evaluation_result` é opcional (nullable) porque, teoricamente,
uma avaliação pode ser recomputada sem re-executar o agente (ex. mudou-se um
avaliador) — vínculo é útil, não obrigatório no MVP.

## Camada de acesso (`engine/persistence/repository.py`)

```
def get_connection() -> psycopg.Connection:
    # lê DATABASE_URL do ambiente, falha explicitamente se ausente

def apply_schema(conn) -> None:
    # executa schema.sql

def save_trace(conn, trace: Trace) -> None:
    # insert em trace + trace_event, tudo em uma transação

def get_trace(conn, trace_id: str) -> Trace | None:
    # reconstrói Trace + events ordenados por sequence

def save_evaluation_result(conn, result: EvaluationResult) -> int:
    # insert, retorna id

def list_evaluation_results(conn, case_id: str | None = None) -> list[EvaluationResult]:
    # filtra por case_id se informado
```

## Variáveis de ambiente

`DATABASE_URL` no formato `postgresql://agentlab:agentlab_dev_only@localhost:5432/agentlab`,
lida via `os.environ["DATABASE_URL"]` — falha explicita (KeyError) se ausente,
não um default silencioso (princípio "falhar explicitamente", seção 3).

## Passos de implementação

1. `docker-compose.yml` na raiz do repo.
2. `.env.example` com `DATABASE_URL` de exemplo.
3. `engine/persistence/schema.sql`.
4. `engine/persistence/repository.py`.
5. `engine/requirements.txt` — adicionar `psycopg[binary]>=3.1`.
6. `contracts/` — os schemas JSON já existentes (`trace.schema.json`,
   `evaluation-result.schema.json`) já documentam o formato; não duplicar,
   só referenciar.
7. `tests/integration/test_repository.py` — testes de integração reais
   (não mockados) contra o Postgres do `docker-compose`.
8. **Passo manual do usuário**: iniciar Docker Desktop, rodar
   `docker compose up -d`, exportar `DATABASE_URL`, então eu rodo os testes.

## Fora deste plano

Tabelas `agent`, `agent_version`, `experiment`, `prompt_version` — dependem do
Experiment Manager (spec futura). Migrations formais (Alembic) — só se o
schema crescer o suficiente para justificar.

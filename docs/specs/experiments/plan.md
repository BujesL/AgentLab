# Plan: Experiment Manager

## Schema adicional (`engine/persistence/schema.sql`, extensão)

```sql
CREATE TABLE IF NOT EXISTS agent (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS agent_version (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agent(id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    code_ref TEXT NOT NULL DEFAULT '',
    UNIQUE (agent_id, version)
);

CREATE TABLE IF NOT EXISTS experiment (
    id TEXT PRIMARY KEY,
    agent_version_id TEXT NOT NULL REFERENCES agent_version(id) ON DELETE CASCADE,
    dataset_id TEXT NOT NULL,
    model TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'running'
);
```

`trace.experiment_id` e `evaluation_result` já existem — `evaluation_result`
precisa ganhar `experiment_id` também (hoje só tem `trace_id`), já que uma
avaliação pode em tese não ter trace mas sempre pertence a um experimento
quando rodada via `--experiment`.

```sql
ALTER TABLE evaluation_result ADD COLUMN IF NOT EXISTS experiment_id TEXT
    REFERENCES experiment(id) ON DELETE SET NULL;
```

## Modelos (Pydantic) — `engine/experiments/models.py`

```
Agent
├── id: str
├── name: str
└── description: str = ""

AgentVersion
├── id: str
├── agent_id: str
├── version: str
└── code_ref: str = ""

Experiment
├── id: str
├── agent_version_id: str
├── dataset_id: str
├── model: str
├── config: dict = {}
└── status: Literal["running", "completed", "failed"] = "running"

ExperimentSummary
├── experiment_id: str
├── total_cases: int
├── passed: int
├── accuracy_pct: float
├── avg_latency_ms: float
└── avg_cost: float
```

## Repositório — `engine/experiments/repository.py`

`get_or_create_agent`, `get_or_create_agent_version`, `create_experiment`,
`get_experiment`, `list_experiments` — mesma abordagem sem ORM do
`engine/persistence/repository.py` (psycopg puro).

## Sumarização — `engine/experiments/summary.py`

```
def summarize_experiment(conn, experiment_id: str) -> ExperimentSummary:
    # SELECT sobre evaluation_result WHERE experiment_id = %s
    # + JOIN com trace (mesmo experiment_id) para latency/cost médios
    # zeros se não houver linhas, nunca erro
```

## Mudança no CLI (`engine/cli.py`)

`evaluate` ganha `--agent`, `--agent-version`, `--experiment` (nome/id)
opcionais. Se nenhum for passado, comportamento idêntico ao MVP (sem
experimento — `experiment_id=None`, como já era). Isso preserva
retrocompatibilidade com os testes existentes de `test_cli.py`.

## Passos de implementação

1. Estender `engine/persistence/schema.sql` com as 3 tabelas novas + ALTER.
2. `engine/experiments/models.py`.
3. `engine/experiments/repository.py`.
4. `engine/experiments/summary.py`.
5. Atualizar `engine/persistence/repository.py::save_trace`/
   `save_evaluation_result` para aceitarem `experiment_id`.
6. Atualizar `engine/cli.py::handle_evaluate` com as novas flags opcionais.
7. `tests/integration/test_experiments.py` — testes reais contra o Neon
   (mesma abordagem de `test_repository.py`, skip sem `DATABASE_URL`).
8. Rodar suíte completa + reaplicar schema no Neon.

## Fora deste plano

`agentlab compare` como comando de CLI, `prompt_version` — specs futuras.

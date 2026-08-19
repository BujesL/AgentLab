# Plan: Prompt Versioning

## Schema (extensão de `engine/persistence/schema.sql`)

```sql
CREATE TABLE IF NOT EXISTS prompt_version (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE
);

ALTER TABLE experiment ADD COLUMN IF NOT EXISTS prompt_version_id TEXT
    REFERENCES prompt_version(id) ON DELETE SET NULL;
```

`content_hash` é `UNIQUE` — é a chave natural de idempotência.

## Modelo (Pydantic) — `engine/prompts/models.py`

```
PromptVersion
├── id: str
├── name: str
├── version: str        # hash abreviado, 12 chars
└── content_hash: str    # SHA-256 completo, hex
```

## Repositório — `engine/prompts/repository.py`

```
def get_or_create_prompt_version(conn, name: str, content: str) -> PromptVersion:
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    # SELECT por content_hash; se existir, retorna; senão, INSERT com
    # version = content_hash[:12]
```

## Mudança no CLI

`evaluate` ganha `--prompt-file <path>` opcional. Se informado: lê o arquivo,
chama `get_or_create_prompt_version(conn, name=Path(path).stem, content=...)`,
guarda `prompt_version_id` na criação do `Experiment` (exige `conn` — ou
seja, só funciona combinado com `--agent`, que já é quando o Experiment é
criado; sem `--agent`, `--prompt-file` é ignorado com aviso, não erro).

## Passos de implementação

1. Estender `schema.sql`.
2. `engine/prompts/models.py`, `engine/prompts/repository.py`.
3. Atualizar `engine/experiments/repository.py::create_experiment` para
   aceitar `prompt_version_id` opcional.
4. Atualizar `engine/cli.py` (`--prompt-file`).
5. `tests/unit/test_prompts.py` — hash determinístico, idempotência (sem
   precisar de banco real, testa só a função de hash + a lógica pura).
6. `tests/integration/test_prompts_repository.py` — get_or_create real
   contra o Neon.
7. Reaplicar schema, rodar testes reais.

## Fora deste plano

UI de diffing, templates — ver "fora do escopo" em spec.md.

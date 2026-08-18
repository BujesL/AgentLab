# Plan: Evaluation Case + Dataset

## Abordagem técnica

- Linguagem: Python (engine, ADR-002), usando **Pydantic v2** para os modelos de
  dados — dá validação de schema "de graça" com mensagens de erro claras, e gera
  JSON Schema exportável (útil depois para o Contract Designer/API em V1).
- Datasets são arquivos **JSON** (não YAML) por simplicidade e porque o exemplo do
  documento-base (seção 10, 24) já usa JSON. Um arquivo por dataset em
  `datasets/<nome>/dataset.json`.
- Validação é uma função pura (`validate_dataset(path) -> ValidationResult`) e
  também um comando de CLI (`engine/cli.py dataset validate <nome>`), reaproveitando
  a mesma função — sem duplicar lógica entre CLI e chamadas programáticas.

## Modelos (Pydantic)

```
EvaluationCase
├── id: str                          # ex. "SD-001"
├── input: str
├── expected_tools: list[str] = []   # vazio = nenhuma tool esperada
├── expected_arguments: dict | None = None
├── expected_answer: dict | None = None
├── expected_behavior: Literal["answer", "refuse", "clarify"] = "answer"
└── requires_approval: bool = False

Dataset
├── id: str
├── name: str
├── version: str                     # semver simples, ex. "0.1.0"
├── description: str
└── cases: list[EvaluationCase]
```

## Regras de validação além do schema

- `id` de `EvaluationCase` deve ser único dentro do dataset.
- Se `expected_behavior == "refuse"`, `expected_answer` deve ser `None`
  (não faz sentido esperar resposta e recusa ao mesmo tempo).
- Se `expected_tools` não é vazio, recomenda-se (não obrigatório) que
  `expected_arguments` esteja presente — validação de aviso (warning), não erro,
  porque casos podem esperar apenas a ferramenta certa sem checar argumentos.

## Passos de implementação

1. `engine/models.py` — modelos Pydantic (`EvaluationCase`, `Dataset`).
2. `engine/datasets.py` — `load_dataset(path)`, `validate_dataset(path)`.
3. `datasets/service-desk-mvp/dataset.json` — dataset inicial (10-15 casos).
4. `tests/unit/test_models.py` — casos válidos/inválidos por campo.
5. `tests/unit/test_datasets.py` — validação de dataset completo, ids duplicados,
   regra de refuse+answer.
6. CLI (`engine/cli.py`) — comando `dataset validate` (esqueleto mínimo; CLI
   completa vem na etapa 9 do roadmap MVP, seção 30).

## Dependências Python novas

- `pydantic>=2` — validação de schema.
- `typer` ou `click` — CLI (decidir na etapa 9; por ora só um `argparse` mínimo
  para não travar esta etapa esperando essa decisão).
- `pytest` — testes.

## Fora deste plano

Contratos de Agent Runner / Provider Adapter (próxima spec), Trace Model (spec
seguinte), Evaluation Engine de métricas (Answer Accuracy/Tool Selection) — este
plano cobre só a representação de dados de entrada (Dataset/Case), não a execução.

# Plan: Token, Latency e Cost Tracking

## Modelos — `engine/usage.py`

```
TokenUsage (Pydantic)
├── prompt_tokens: int = 0
├── completion_tokens: int = 0
└── total_tokens (property) = prompt_tokens + completion_tokens
```

## Mudanças em `engine/providers/base.py`

`ToolCallRequest` e `FinalAnswer` ganham campo opcional `usage: TokenUsage | None
= None`. Um `ProviderAdapter` real reportaria isso a partir da resposta bruta da
API (ex. `response.usage.input_tokens`); o `MockProviderAdapter` de teste pode
opcionalmente incluir `usage` no script para testar a agregação.

## Mudanças em `engine/runner.py`

`RunResult` ganha campo opcional `token_usage: TokenUsage | None = None`.
`AgentRunner.run()` acumula `prompt_tokens`/`completion_tokens` de cada `step`
que tiver `usage` não-nulo; se nenhum passo reportou usage, o campo final
permanece `None` (não inventamos zero — zero e "não reportado" são semânticas
diferentes).

## `engine/cost.py`

```
PRICING = {
    "mock": {"prompt_per_1k": 0.0, "completion_per_1k": 0.0},
    # valores de exemplo — NÃO são tarifário oficial, ver spec.md
    "claude-placeholder": {"prompt_per_1k": 0.003, "completion_per_1k": 0.015},
}

def estimate_cost(usage: TokenUsage | None, model: str = "mock") -> float:
    if usage is None:
        return 0.0
    pricing = PRICING.get(model, PRICING["mock"])
    return (usage.prompt_tokens / 1000) * pricing["prompt_per_1k"] + \
           (usage.completion_tokens / 1000) * pricing["completion_per_1k"]
```

## Mudanças em `engine/traces.py`

`build_trace(run_result, model="mock")` passa a aceitar `model` (para escolher
a tabela de preço) e popula:
- `token_usage = run_result.token_usage.total_tokens if run_result.token_usage else None`
- `cost = estimate_cost(run_result.token_usage, model) if run_result.token_usage else None`

## Passos de implementação

1. `engine/usage.py` — `TokenUsage`.
2. Atualizar `engine/providers/base.py` — campo `usage` em `ToolCallRequest`/`FinalAnswer`.
3. Atualizar `engine/runner.py` — agregação em `RunResult.token_usage`.
4. `engine/cost.py` — `PRICING`, `estimate_cost`.
5. Atualizar `engine/traces.py` — propagar `token_usage`/`cost` no `Trace`.
6. `contracts/token-usage.schema.json`.
7. `tests/unit/test_cost.py` cobrindo os 6 critérios de aceitação.
8. Rodar suíte completa (garantir que testes anteriores de runner/traces
   continuam passando com os campos novos opcionais).

## Fora deste plano

Cost tracking agregado por experimento — depende do Experiment Manager
(spec futura).

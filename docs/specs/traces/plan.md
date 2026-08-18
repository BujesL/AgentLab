# Plan: Trace Model

## Mudança retroativa no Agent Runner

`engine/runner.py` passa a anexar `"timestamp": time.time()` em cada dict de
`history` (que vira `raw_events`), e a registrar também o evento inicial
(`input`) e o evento final (`final_answer` ou `blocked_pending_approval`) — hoje
só tool_call_request/tool_result eram registrados. Isso é uma extensão aditiva:
não quebra os testes existentes de `test_runner.py` (eles não fazem asserção
sobre `raw_events`).

## Modelos (Pydantic) — `engine/traces.py`

```
TraceEvent
├── sequence: int
├── type: Literal["input","tool_call_request","tool_result","final_answer","blocked_pending_approval"]
├── payload: dict
└── timestamp: float          # epoch seconds

Trace
├── id: str                   # uuid4, gerado em build_trace
├── experiment_id: str | None = None   # populado quando Experiment Manager existir
├── case_id: str
├── started_at: float
├── duration_ms: float
├── token_usage: int | None = None     # populado na etapa de cost tracking
├── cost: float | None = None
└── events: list[TraceEvent]
```

## Função principal

```
def build_trace(run_result: RunResult) -> Trace:
    events = []
    for i, raw in enumerate(run_result.raw_events):
        payload = {k: v for k, v in raw.items() if k not in ("type", "timestamp")}
        _assert_no_forbidden_keys(payload)
        events.append(TraceEvent(sequence=i, type=raw["type"],
                                  payload=payload, timestamp=raw["timestamp"]))
    started_at = events[0].timestamp
    duration_ms = (events[-1].timestamp - started_at) * 1000
    return Trace(id=str(uuid4()), case_id=run_result.case_id,
                 started_at=started_at, duration_ms=duration_ms, events=events)
```

`_assert_no_forbidden_keys` percorre o payload recursivamente (incluindo dicts
aninhados, ex. `arguments`/`result`) e levanta erro se encontrar as chaves
proibidas — validação defensiva mesmo sem uso real ainda.

## Passos de implementação

1. Atualizar `engine/runner.py` — adicionar timestamps e eventos `input`/final.
2. `engine/traces.py` — `TraceEvent`, `Trace`, `build_trace`,
   `_assert_no_forbidden_keys`.
3. `docs/architecture/decisions/ADR-004-traces-sem-chain-of-thought.md`.
4. `tests/unit/test_traces.py` cobrindo os 6 critérios de aceitação.
5. Rodar suíte completa (não só os testes novos) para garantir que a mudança
   retroativa no runner não quebrou nada.

## Fora deste plano

Persistência PostgreSQL do trace, Trace Viewer (UI), Evaluation Engine
(métricas) — specs seguintes.

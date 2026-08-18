from typing import Literal
from uuid import uuid4

from pydantic import BaseModel

from engine.cost import estimate_cost
from engine.runner import RunResult

FORBIDDEN_KEYS = {"reasoning", "thought", "chain_of_thought"}

TraceEventType = Literal[
    "input",
    "tool_call_request",
    "tool_result",
    "final_answer",
    "blocked_pending_approval",
]


class TraceEvent(BaseModel):
    model_config = {"extra": "forbid"}

    sequence: int
    type: TraceEventType
    payload: dict
    timestamp: float


class Trace(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    experiment_id: str | None = None
    case_id: str
    started_at: float
    duration_ms: float
    token_usage: int | None = None
    cost: float | None = None
    events: list[TraceEvent]


def _assert_no_forbidden_keys(payload: dict) -> None:
    for key, value in payload.items():
        if key.lower() in FORBIDDEN_KEYS:
            raise ValueError(f"trace payload contains forbidden key: {key}")
        if isinstance(value, dict):
            _assert_no_forbidden_keys(value)


def build_trace(run_result: RunResult, model: str = "mock") -> Trace:
    if not run_result.raw_events:
        raise ValueError(f"run_result for case {run_result.case_id} has no raw_events")

    events: list[TraceEvent] = []
    for i, raw in enumerate(run_result.raw_events):
        payload = {k: v for k, v in raw.items() if k not in ("type", "timestamp")}
        _assert_no_forbidden_keys(payload)
        events.append(
            TraceEvent(
                sequence=i,
                type=raw["type"],
                payload=payload,
                timestamp=raw["timestamp"],
            )
        )

    started_at = events[0].timestamp
    duration_ms = max(0.0, (events[-1].timestamp - started_at) * 1000)

    token_usage = run_result.token_usage.total_tokens if run_result.token_usage else None
    cost = estimate_cost(run_result.token_usage, model) if run_result.token_usage else None

    return Trace(
        id=str(uuid4()),
        case_id=run_result.case_id,
        started_at=started_at,
        duration_ms=duration_ms,
        token_usage=token_usage,
        cost=cost,
        events=events,
    )

import json
from pathlib import Path

from engine.providers.base import FinalAnswer, ProviderStep, ToolCallRequest


def _parse_step(raw: dict) -> ProviderStep:
    kind = raw.get("kind")
    if kind == "tool_call_request":
        return ToolCallRequest(tool_name=raw["tool_name"], arguments=raw.get("arguments", {}))
    if kind == "final_answer":
        return FinalAnswer(answer=raw.get("answer"))
    raise ValueError(f"unknown step kind: {kind!r}")


def load_scripts(path: Path) -> dict[str, list[ProviderStep]]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    return {
        case_id: [_parse_step(step) for step in steps] for case_id, steps in raw.items()
    }

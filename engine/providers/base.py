from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from engine.tools.models import ToolSpec


@dataclass
class ToolCallRequest:
    kind: Literal["tool_call_request"] = "tool_call_request"
    tool_name: str = ""
    arguments: dict | None = None


@dataclass
class FinalAnswer:
    kind: Literal["final_answer"] = "final_answer"
    answer: dict | None = None


ProviderStep = ToolCallRequest | FinalAnswer


class ProviderAdapter(ABC):
    """Abstracts a single reasoning step of an LLM-backed agent.

    Concrete implementations (mock, Claude, OpenAI, ...) are interchangeable
    from the AgentRunner's point of view — it never imports a specific
    provider directly (ADR-001, ADR-002).
    """

    @abstractmethod
    def step(
        self, input: str, tools: list[ToolSpec], history: list[dict]
    ) -> ProviderStep:
        raise NotImplementedError

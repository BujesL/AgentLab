from dataclasses import dataclass

from engine.providers.base import ProviderAdapter
from engine.tools.registry import ToolRegistry


@dataclass
class AgentSpec:
    """One specialist agent: its own provider (reasoning) and its own tool
    registry (scope). A specialist never sees another specialist's tools —
    that boundary is what evaluate_handoff checks for leakage.
    """

    name: str
    provider: ProviderAdapter
    registry: ToolRegistry
    system_prompt: str | None = None

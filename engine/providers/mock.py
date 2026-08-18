from engine.providers.base import ProviderStep
from engine.tools.models import ToolSpec


class MockProviderAdapter:
    """Test double for ProviderAdapter: replays a fixed script of steps.

    Not a simulation of a real LLM's reasoning — a deterministic double used to
    validate AgentRunner and, later, the Evaluation Engine, independent of LLM
    variability. A real provider (Claude, etc.) is a separate implementation of
    the same ProviderAdapter interface. One instance is scripted for one case
    at a time (create a fresh instance per case in tests/runs).
    """

    def __init__(self, script: list[ProviderStep]) -> None:
        self._script = script
        self._cursor = 0

    def step(self, input: str, tools: list[ToolSpec], history: list[dict]) -> ProviderStep:
        if self._cursor >= len(self._script):
            raise RuntimeError("mock provider script exhausted")
        step = self._script[self._cursor]
        self._cursor += 1
        return step

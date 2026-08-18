from engine.tools.models import ToolSpec


class ToolRegistry:
    """Holds ToolSpec definitions and mocks their execution.

    Per ADR-003, no real tool execution ever happens here — execute_mocked
    always returns a caller-supplied stub, never touches a network or database.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._stubs: dict[str, dict] = {}

    def register(self, tool: ToolSpec, stub_result: dict | None = None) -> None:
        self._tools[tool.name] = tool
        if stub_result is not None:
            self._stubs[tool.name] = stub_result

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        return self._tools[name]

    def enabled_tools(self) -> list[ToolSpec]:
        return [t for t in self._tools.values() if t.enabled_for_evaluation]

    def execute_mocked(self, name: str, arguments: dict) -> dict:
        tool = self.get(name)
        if not tool.enabled_for_evaluation:
            raise ValueError(f"tool {name} is not enabled for evaluation")
        return self._stubs.get(name, {})

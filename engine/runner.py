from pydantic import BaseModel

from engine.models import EvaluationCase
from engine.providers.base import FinalAnswer, ProviderAdapter, ToolCallRequest
from engine.tools.models import ToolCall
from engine.tools.registry import ToolRegistry


class RunResult(BaseModel):
    model_config = {"extra": "forbid"}

    case_id: str
    tool_calls: list[ToolCall] = []
    final_answer: dict | None = None
    blocked_pending_approval: bool = False
    raw_events: list[dict] = []


class AgentRunner:
    def __init__(self, max_iterations: int = 5) -> None:
        self.max_iterations = max_iterations

    def run(
        self,
        case: EvaluationCase,
        provider: ProviderAdapter,
        registry: ToolRegistry,
    ) -> RunResult:
        history: list[dict] = []
        tool_calls: list[ToolCall] = []

        for _ in range(self.max_iterations):
            step = provider.step(case.input, registry.enabled_tools(), history)

            if isinstance(step, FinalAnswer):
                return RunResult(
                    case_id=case.id,
                    tool_calls=tool_calls,
                    final_answer=step.answer,
                    raw_events=history,
                )

            assert isinstance(step, ToolCallRequest)
            tool = registry.get(step.tool_name)
            arguments = step.arguments or {}
            history.append(
                {"type": "tool_call_request", "tool": step.tool_name, "arguments": arguments}
            )

            if tool.requires_approval:
                return RunResult(
                    case_id=case.id,
                    tool_calls=tool_calls,
                    blocked_pending_approval=True,
                    raw_events=history,
                )

            result = registry.execute_mocked(step.tool_name, arguments)
            tool_calls.append(
                ToolCall(tool_name=step.tool_name, arguments=arguments, result=result)
            )
            history.append(
                {"type": "tool_result", "tool": step.tool_name, "result": result}
            )

        raise RuntimeError(f"max_iterations exceeded for case {case.id}")

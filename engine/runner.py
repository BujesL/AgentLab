import time

from pydantic import BaseModel

from engine.models import EvaluationCase
from engine.providers.base import FinalAnswer, ProviderAdapter, ProviderStep, ToolCallRequest
from engine.tools.models import ToolCall
from engine.tools.registry import ToolRegistry
from engine.usage import TokenUsage


class RunResult(BaseModel):
    model_config = {"extra": "forbid"}

    case_id: str
    tool_calls: list[ToolCall] = []
    final_answer: dict | None = None
    blocked_pending_approval: bool = False
    raw_events: list[dict] = []
    token_usage: TokenUsage | None = None


class _UsageAccumulator:
    """Tracks whether any step reported usage; None stays None if nothing was reported."""

    def __init__(self) -> None:
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._any_reported = False

    def add(self, step: ProviderStep) -> None:
        if step.usage is None:
            return
        self._any_reported = True
        self._prompt_tokens += step.usage.prompt_tokens
        self._completion_tokens += step.usage.completion_tokens

    def result(self) -> TokenUsage | None:
        if not self._any_reported:
            return None
        return TokenUsage(
            prompt_tokens=self._prompt_tokens, completion_tokens=self._completion_tokens
        )


class AgentRunner:
    def __init__(self, max_iterations: int = 5) -> None:
        self.max_iterations = max_iterations

    def run(
        self,
        case: EvaluationCase,
        provider: ProviderAdapter,
        registry: ToolRegistry,
    ) -> RunResult:
        history: list[dict] = [{"type": "input", "input": case.input, "timestamp": time.time()}]
        tool_calls: list[ToolCall] = []
        usage_acc = _UsageAccumulator()

        for _ in range(self.max_iterations):
            step = provider.step(case.input, registry.enabled_tools(), history)
            usage_acc.add(step)

            if isinstance(step, FinalAnswer):
                history.append(
                    {"type": "final_answer", "answer": step.answer, "timestamp": time.time()}
                )
                return RunResult(
                    case_id=case.id,
                    tool_calls=tool_calls,
                    final_answer=step.answer,
                    raw_events=history,
                    token_usage=usage_acc.result(),
                )

            assert isinstance(step, ToolCallRequest)
            tool = registry.get(step.tool_name)
            arguments = step.arguments or {}
            history.append(
                {
                    "type": "tool_call_request",
                    "tool": step.tool_name,
                    "arguments": arguments,
                    "timestamp": time.time(),
                }
            )

            if tool.requires_approval:
                history.append(
                    {
                        "type": "blocked_pending_approval",
                        "tool": step.tool_name,
                        "timestamp": time.time(),
                    }
                )
                return RunResult(
                    case_id=case.id,
                    tool_calls=tool_calls,
                    blocked_pending_approval=True,
                    raw_events=history,
                    token_usage=usage_acc.result(),
                )

            result = registry.execute_mocked(step.tool_name, arguments)
            tool_calls.append(
                ToolCall(tool_name=step.tool_name, arguments=arguments, result=result)
            )
            history.append(
                {
                    "type": "tool_result",
                    "tool": step.tool_name,
                    "result": result,
                    "timestamp": time.time(),
                }
            )

        raise RuntimeError(f"max_iterations exceeded for case {case.id}")

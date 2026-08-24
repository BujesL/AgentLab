import time

from pydantic import BaseModel

from engine.models import EvaluationCase
from engine.providers.base import FinalAnswer, ProviderAdapter, ProviderStep, ToolCallRequest
from engine.rag.retriever import Retriever
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
    retrieved_context: list[str] | None = None
    agent_path: list[str] = []


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
        retriever: Retriever | None = None,
    ) -> RunResult:
        history: list[dict] = [{"type": "input", "input": case.input, "timestamp": time.time()}]
        tool_calls: list[ToolCall] = []
        usage_acc = _UsageAccumulator()

        effective_input = case.input
        retrieved_context: list[str] | None = None
        # case.context (manually authored, e.g. rag-groundedness-mvp) always wins over
        # automatic retrieval — keeps hand-written test fixtures deterministic even
        # when a --rag retriever is also passed.
        if retriever is not None and not case.context:
            retrieved_context = retriever.retrieve(case.input)
            if retrieved_context:
                context_block = "\n".join(f"- {p}" for p in retrieved_context)
                effective_input = f"Contexto:\n{context_block}\n\nPergunta: {case.input}"
                history.append(
                    {
                        "type": "retrieval",
                        "query": case.input,
                        "passages": retrieved_context,
                        "timestamp": time.time(),
                    }
                )

        for _ in range(self.max_iterations):
            step = provider.step(effective_input, registry.enabled_tools(), history)
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
                    retrieved_context=retrieved_context,
                )

            assert isinstance(step, ToolCallRequest)
            arguments = step.arguments or {}
            history.append(
                {
                    "type": "tool_call_request",
                    "tool": step.tool_name,
                    "arguments": arguments,
                    "timestamp": time.time(),
                }
            )

            try:
                tool = registry.get(step.tool_name)
            except KeyError:
                # A tool name outside this registry — either a real provider
                # hallucinating, or (found while scaling multi-agent-mvp) a
                # misrouted case landing on a specialist whose registry doesn't
                # have the tool it needs. Record it and stop, same terminal shape
                # as blocked_pending_approval, instead of an unhandled KeyError
                # that used to crash the whole evaluate/evaluate-multi-agent batch
                # (every remaining case would be skipped, not just this one).
                tool_calls.append(
                    ToolCall(tool_name=step.tool_name, arguments=arguments, result=None)
                )
                return RunResult(
                    case_id=case.id,
                    tool_calls=tool_calls,
                    raw_events=history,
                    token_usage=usage_acc.result(),
                    retrieved_context=retrieved_context,
                )

            if tool.requires_approval:
                history.append(
                    {
                        "type": "blocked_pending_approval",
                        "tool": step.tool_name,
                        "timestamp": time.time(),
                    }
                )
                # Recorded with result=None: the tool was selected/attempted but
                # never executed (ADR-003). Evaluators (e.g. tool_selection,
                # tool_argument_accuracy) need to see which tool was chosen even
                # when approval blocks execution — see docs/specs/cli/tasks.md.
                tool_calls.append(
                    ToolCall(tool_name=step.tool_name, arguments=arguments, result=None)
                )
                return RunResult(
                    case_id=case.id,
                    tool_calls=tool_calls,
                    blocked_pending_approval=True,
                    raw_events=history,
                    token_usage=usage_acc.result(),
                    retrieved_context=retrieved_context,
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

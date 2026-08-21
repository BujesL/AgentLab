import pytest

from engine.models import EvaluationCase
from engine.providers.base import FinalAnswer, ToolCallRequest
from engine.providers.mock import MockProviderAdapter
from engine.runner import AgentRunner
from engine.tools.models import ToolSpec
from engine.tools.registry import ToolRegistry


def make_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="get_tickets",
            description="List tickets",
            input_schema={"type": "object"},
        ),
        stub_result={"count": 4},
    )
    registry.register(
        ToolSpec(
            name="delete_all_tickets",
            description="Delete all tickets",
            input_schema={"type": "object"},
            risk_level="high",
            requires_approval=True,
        ),
    )
    return registry


def test_case_without_tools_returns_final_answer_directly():
    case = EvaluationCase(id="SD-004", input="Qual o horário de funcionamento?")
    provider = MockProviderAdapter([FinalAnswer(answer={"text": "24/7"})])
    runner = AgentRunner()

    result = runner.run(case, provider, make_registry())

    assert result.tool_calls == []
    assert result.final_answer == {"text": "24/7"}
    assert not result.blocked_pending_approval


def test_case_with_tool_call_executes_mocked_tool_and_returns_answer():
    case = EvaluationCase(
        id="SD-001",
        input="Quais chamados urgentes estão atrasados?",
        expected_tools=["get_tickets"],
    )
    provider = MockProviderAdapter(
        [
            ToolCallRequest(tool_name="get_tickets", arguments={"priority": "urgent"}),
            FinalAnswer(answer={"count": 4}),
        ]
    )
    runner = AgentRunner()

    result = runner.run(case, provider, make_registry())

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "get_tickets"
    assert result.tool_calls[0].result == {"count": 4}
    assert result.final_answer == {"count": 4}


def test_requires_approval_tool_is_blocked_not_executed():
    case = EvaluationCase(
        id="SD-011",
        input="Cancele a assinatura da empresa inteira.",
        expected_behavior="refuse",
        requires_approval=True,
    )
    provider = MockProviderAdapter(
        [ToolCallRequest(tool_name="delete_all_tickets", arguments={})]
    )
    runner = AgentRunner()

    result = runner.run(case, provider, make_registry())

    assert result.blocked_pending_approval
    assert result.final_answer is None
    # The tool was selected/attempted but never executed (ADR-003): recorded
    # with result=None so evaluators can still see which tool was chosen.
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "delete_all_tickets"
    assert result.tool_calls[0].result is None


def test_tool_calls_captured_in_order():
    case = EvaluationCase(id="SD-001", input="x", expected_tools=["get_tickets"])
    provider = MockProviderAdapter(
        [
            ToolCallRequest(tool_name="get_tickets", arguments={"a": 1}),
            ToolCallRequest(tool_name="get_tickets", arguments={"a": 2}),
            FinalAnswer(answer={"ok": True}),
        ]
    )
    runner = AgentRunner()

    result = runner.run(case, provider, make_registry())

    assert [c.arguments for c in result.tool_calls] == [{"a": 1}, {"a": 2}]


def test_registry_rejects_tool_without_input_schema():
    with pytest.raises(Exception):
        ToolSpec(name="bad_tool", description="desc")  # missing input_schema


def test_max_iterations_exceeded_raises():
    case = EvaluationCase(id="SD-001", input="x", expected_tools=["get_tickets"])
    provider = MockProviderAdapter(
        [ToolCallRequest(tool_name="get_tickets", arguments={}) for _ in range(3)]
    )
    runner = AgentRunner(max_iterations=2)

    with pytest.raises(RuntimeError):
        runner.run(case, provider, make_registry())


# --- Retrieval (--rag) --------------------------------------------------------


class _RecordingProvider:
    """Fake provider that records the `input` string it was called with, so tests
    can assert on the effective prompt AgentRunner built (unlike MockProviderAdapter,
    which ignores `input` entirely)."""

    def __init__(self, script):
        self._script = list(script)
        self.received_inputs: list[str] = []

    def step(self, input, tools, history):
        self.received_inputs.append(input)
        return self._script.pop(0)


class _FakeRetriever:
    def __init__(self, passages: list[str]) -> None:
        self.passages = passages
        self.queries: list[str] = []

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        self.queries.append(query)
        return self.passages


def test_retriever_injects_context_into_effective_input():
    case = EvaluationCase(id="RAG-001", input="Em quantos dias posso pedir reembolso?")
    provider = _RecordingProvider([FinalAnswer(answer={"text": "30 dias"})])
    retriever = _FakeRetriever(["A política de reembolso permite devolução em 30 dias."])
    runner = AgentRunner()

    result = runner.run(case, provider, make_registry(), retriever=retriever)

    assert retriever.queries == [case.input]
    assert "Contexto:" in provider.received_inputs[0]
    assert "política de reembolso" in provider.received_inputs[0]
    assert case.input in provider.received_inputs[0]
    assert result.retrieved_context == retriever.passages


def test_manually_authored_context_wins_over_retriever():
    case = EvaluationCase(
        id="RAG-002", input="pergunta", context=["contexto manual do autor do dataset"]
    )
    provider = _RecordingProvider([FinalAnswer(answer={"text": "ok"})])
    retriever = _FakeRetriever(["contexto vindo do retriever automático"])
    runner = AgentRunner()

    result = runner.run(case, provider, make_registry(), retriever=retriever)

    assert retriever.queries == []
    assert provider.received_inputs[0] == case.input
    assert result.retrieved_context is None


def test_no_retriever_leaves_input_unchanged():
    case = EvaluationCase(id="SD-004", input="pergunta qualquer")
    provider = _RecordingProvider([FinalAnswer(answer={"text": "resposta"})])
    runner = AgentRunner()

    result = runner.run(case, provider, make_registry())

    assert provider.received_inputs[0] == case.input
    assert result.retrieved_context is None

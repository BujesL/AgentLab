import pytest

from engine.models import EvaluationCase
from engine.providers.base import FinalAnswer, ToolCallRequest
from engine.providers.mock import MockProviderAdapter
from engine.runner import AgentRunner
from engine.tools.models import ToolSpec
from engine.tools.registry import ToolRegistry
from engine.traces import build_trace


def make_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(name="get_tickets", description="List tickets", input_schema={"type": "object"}),
        stub_result={"count": 4},
    )
    registry.register(
        ToolSpec(
            name="delete_all_tickets",
            description="Delete all tickets",
            input_schema={"type": "object"},
            requires_approval=True,
        ),
    )
    return registry


def test_trace_sequence_starts_at_zero_and_increments():
    case = EvaluationCase(id="SD-004", input="Qual o horário?")
    provider = MockProviderAdapter([FinalAnswer(answer={"text": "24/7"})])
    result = AgentRunner().run(case, provider, make_registry())

    trace = build_trace(result)

    assert [e.sequence for e in trace.events] == list(range(len(trace.events)))


def test_first_event_is_input():
    case = EvaluationCase(id="SD-004", input="Qual o horário?")
    provider = MockProviderAdapter([FinalAnswer(answer={"text": "24/7"})])
    result = AgentRunner().run(case, provider, make_registry())

    trace = build_trace(result)

    assert trace.events[0].type == "input"
    assert trace.events[0].payload == {"input": "Qual o horário?"}


def test_last_event_reflects_final_answer_outcome():
    case = EvaluationCase(id="SD-004", input="Qual o horário?")
    provider = MockProviderAdapter([FinalAnswer(answer={"text": "24/7"})])
    result = AgentRunner().run(case, provider, make_registry())

    trace = build_trace(result)

    assert trace.events[-1].type == "final_answer"
    assert trace.events[-1].payload == {"answer": {"text": "24/7"}}


def test_last_event_reflects_blocked_pending_approval_outcome():
    case = EvaluationCase(id="SD-011", input="Cancele tudo.", requires_approval=True)
    provider = MockProviderAdapter([ToolCallRequest(tool_name="delete_all_tickets", arguments={})])
    result = AgentRunner().run(case, provider, make_registry())

    trace = build_trace(result)

    assert trace.events[-1].type == "blocked_pending_approval"


def test_duration_ms_non_negative_and_matches_span():
    case = EvaluationCase(id="SD-004", input="x")
    provider = MockProviderAdapter([FinalAnswer(answer={"ok": True})])
    result = AgentRunner().run(case, provider, make_registry())

    trace = build_trace(result)

    expected = max(0.0, (trace.events[-1].timestamp - trace.events[0].timestamp) * 1000)
    assert trace.duration_ms >= 0
    assert trace.duration_ms == pytest.approx(expected)


def test_forbidden_keys_rejected():
    from engine.traces import _assert_no_forbidden_keys

    with pytest.raises(ValueError):
        _assert_no_forbidden_keys({"reasoning": "secret chain of thought"})

    with pytest.raises(ValueError):
        _assert_no_forbidden_keys({"answer": {"chain_of_thought": "nope"}})

    _assert_no_forbidden_keys({"answer": {"count": 4}})  # should not raise


def test_multiple_tool_calls_interleaved_in_order():
    case = EvaluationCase(id="SD-001", input="x", expected_tools=["get_tickets"])
    provider = MockProviderAdapter(
        [
            ToolCallRequest(tool_name="get_tickets", arguments={"a": 1}),
            ToolCallRequest(tool_name="get_tickets", arguments={"a": 2}),
            FinalAnswer(answer={"ok": True}),
        ]
    )
    result = AgentRunner().run(case, provider, make_registry())

    trace = build_trace(result)

    types = [e.type for e in trace.events]
    assert types == [
        "input",
        "tool_call_request",
        "tool_result",
        "tool_call_request",
        "tool_result",
        "final_answer",
    ]

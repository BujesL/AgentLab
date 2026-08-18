from engine.cost import estimate_cost
from engine.models import EvaluationCase
from engine.providers.base import FinalAnswer, ToolCallRequest
from engine.providers.mock import MockProviderAdapter
from engine.runner import AgentRunner
from engine.tools.models import ToolSpec
from engine.tools.registry import ToolRegistry
from engine.traces import build_trace
from engine.usage import TokenUsage


def make_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(name="get_tickets", description="List tickets", input_schema={"type": "object"}),
        stub_result={"count": 4},
    )
    return registry


def test_no_usage_reported_leaves_token_usage_and_cost_none():
    case = EvaluationCase(id="SD-004", input="x")
    provider = MockProviderAdapter([FinalAnswer(answer={"ok": True})])
    result = AgentRunner().run(case, provider, make_registry())

    assert result.token_usage is None

    trace = build_trace(result)
    assert trace.token_usage is None
    assert trace.cost is None


def test_usage_aggregated_across_multiple_steps():
    case = EvaluationCase(id="SD-001", input="x", expected_tools=["get_tickets"])
    provider = MockProviderAdapter(
        [
            ToolCallRequest(
                tool_name="get_tickets",
                arguments={},
                usage=TokenUsage(prompt_tokens=10, completion_tokens=5),
            ),
            FinalAnswer(
                answer={"count": 4},
                usage=TokenUsage(prompt_tokens=20, completion_tokens=8),
            ),
        ]
    )
    result = AgentRunner().run(case, provider, make_registry())

    assert result.token_usage is not None
    assert result.token_usage.prompt_tokens == 30
    assert result.token_usage.completion_tokens == 13
    assert result.token_usage.total_tokens == 43


def test_estimate_cost_zero_for_mock_model_even_with_tokens():
    usage = TokenUsage(prompt_tokens=1000, completion_tokens=1000)
    assert estimate_cost(usage, model="mock") == 0.0


def test_estimate_cost_positive_for_priced_model():
    usage = TokenUsage(prompt_tokens=1000, completion_tokens=1000)
    cost = estimate_cost(usage, model="claude-placeholder")
    assert cost > 0.0


def test_estimate_cost_unknown_model_falls_back_to_mock_pricing():
    usage = TokenUsage(prompt_tokens=1000, completion_tokens=1000)
    cost = estimate_cost(usage, model="some-unknown-model")
    assert cost == 0.0


def test_build_trace_propagates_token_usage_and_cost():
    case = EvaluationCase(id="SD-001", input="x", expected_tools=["get_tickets"])
    provider = MockProviderAdapter(
        [
            ToolCallRequest(
                tool_name="get_tickets",
                arguments={},
                usage=TokenUsage(prompt_tokens=100, completion_tokens=50),
            ),
            FinalAnswer(answer={"count": 4}),
        ]
    )
    result = AgentRunner().run(case, provider, make_registry())

    trace = build_trace(result, model="claude-placeholder")

    assert trace.token_usage == 150
    assert trace.cost > 0.0

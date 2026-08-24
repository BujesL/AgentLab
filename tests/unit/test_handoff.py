from engine.evaluators.handoff import evaluate_handoff
from engine.models import EvaluationCase
from engine.multi_agent.models import AgentSpec
from engine.providers.mock import MockProviderAdapter
from engine.runner import RunResult
from engine.tools.models import ToolCall, ToolSpec
from engine.tools.registry import ToolRegistry


def make_specialists() -> dict[str, AgentSpec]:
    billing_registry = ToolRegistry()
    billing_registry.register(
        ToolSpec(name="get_invoice", description="Get invoice", input_schema={"type": "object"})
    )
    technical_registry = ToolRegistry()
    technical_registry.register(
        ToolSpec(name="restart_session", description="Restart session", input_schema={"type": "object"})
    )
    return {
        "billing_agent": AgentSpec(name="billing_agent", provider=MockProviderAdapter([]), registry=billing_registry),
        "technical_agent": AgentSpec(name="technical_agent", provider=MockProviderAdapter([]), registry=technical_registry),
    }


def test_passes_trivially_when_no_expected_agent():
    case = EvaluationCase(id="SD-001", input="qualquer coisa")
    result = RunResult(case_id=case.id)

    score = evaluate_handoff(case, result)

    assert score.metric == "handoff"
    assert score.passed is True
    assert score.score == 1.0


def test_passes_when_routed_to_expected_agent():
    case = EvaluationCase(id="MA-001", input="fatura", expected_agent="billing_agent")
    result = RunResult(case_id=case.id, agent_path=["router", "billing_agent"])

    score = evaluate_handoff(case, result, make_specialists())

    assert score.passed is True


def test_fails_when_routed_to_wrong_agent():
    case = EvaluationCase(id="MA-002", input="fatura", expected_agent="billing_agent")
    result = RunResult(case_id=case.id, agent_path=["router", "technical_agent"])

    score = evaluate_handoff(case, result, make_specialists())

    assert score.passed is False
    assert "billing_agent" in score.reason
    assert "technical_agent" in score.reason


def test_fails_when_router_produced_no_agent():
    case = EvaluationCase(id="MA-003", input="fatura", expected_agent="billing_agent")
    result = RunResult(case_id=case.id, agent_path=["router"])

    score = evaluate_handoff(case, result, make_specialists())

    assert score.passed is False


def test_fails_when_specialist_calls_tool_outside_its_scope():
    case = EvaluationCase(id="MA-004", input="fatura", expected_agent="billing_agent")
    result = RunResult(
        case_id=case.id,
        agent_path=["router", "billing_agent"],
        tool_calls=[ToolCall(tool_name="restart_session", arguments={}, result={})],
    )

    score = evaluate_handoff(case, result, make_specialists())

    assert score.passed is False
    assert "restart_session" in score.reason


def test_ignores_scope_check_when_specialists_not_provided():
    case = EvaluationCase(id="MA-005", input="fatura", expected_agent="billing_agent")
    result = RunResult(
        case_id=case.id,
        agent_path=["router", "billing_agent"],
        tool_calls=[ToolCall(tool_name="restart_session", arguments={}, result={})],
    )

    score = evaluate_handoff(case, result)

    assert score.passed is True

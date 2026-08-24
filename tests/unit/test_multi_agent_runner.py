from engine.models import EvaluationCase
from engine.multi_agent.models import AgentSpec
from engine.multi_agent.router import RoutingError
from engine.multi_agent.runner import MultiAgentRunner
from engine.providers.base import FinalAnswer
from engine.providers.mock import MockProviderAdapter
from engine.tools.models import ToolSpec
from engine.tools.registry import ToolRegistry


class _FakeRouter:
    def __init__(self, choice: str) -> None:
        self.choice = choice
        self.calls: list[tuple[str, list[str]]] = []

    def route(self, input: str, specialists: list[str]) -> str:
        self.calls.append((input, specialists))
        return self.choice


class _FailingRouter:
    def route(self, input: str, specialists: list[str]) -> str:
        raise RoutingError("boom")


def make_specialists() -> dict[str, AgentSpec]:
    billing_registry = ToolRegistry()
    billing_registry.register(
        ToolSpec(name="get_invoice", description="Get invoice", input_schema={"type": "object"})
    )
    return {
        "billing_agent": AgentSpec(
            name="billing_agent",
            provider=MockProviderAdapter([FinalAnswer(answer={"text": "R$ 100"})]),
            registry=billing_registry,
        ),
    }


def test_delegates_to_chosen_specialist():
    case = EvaluationCase(id="MA-001", input="fatura", expected_agent="billing_agent")
    router = _FakeRouter("billing_agent")
    runner = MultiAgentRunner()

    result = runner.run(case, router, make_specialists())

    assert result.agent_path == ["router", "billing_agent"]
    assert result.final_answer == {"text": "R$ 100"}
    assert router.calls == [(case.input, ["billing_agent"])]


def test_handoff_event_recorded_before_specialist_events():
    case = EvaluationCase(id="MA-001", input="fatura", expected_agent="billing_agent")
    runner = MultiAgentRunner()

    result = runner.run(case, _FakeRouter("billing_agent"), make_specialists())

    assert result.raw_events[0]["type"] == "handoff"
    assert result.raw_events[0]["to"] == "billing_agent"
    assert result.raw_events[1]["type"] == "input"


def test_unknown_agent_chosen_by_router_does_not_crash():
    case = EvaluationCase(id="MA-001", input="fatura", expected_agent="billing_agent")
    runner = MultiAgentRunner()

    result = runner.run(case, _FakeRouter("nonexistent_agent"), make_specialists())

    assert result.agent_path == ["router", "nonexistent_agent"]
    assert result.final_answer is None


def test_router_failure_does_not_crash():
    case = EvaluationCase(id="MA-001", input="fatura", expected_agent="billing_agent")
    runner = MultiAgentRunner()

    result = runner.run(case, _FailingRouter(), make_specialists())

    assert result.agent_path == ["router"]
    assert result.final_answer is None

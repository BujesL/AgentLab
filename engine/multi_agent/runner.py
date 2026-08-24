import time

from engine.models import EvaluationCase
from engine.multi_agent.models import AgentSpec
from engine.multi_agent.router import Router, RoutingError
from engine.runner import AgentRunner, RunResult


class MultiAgentRunner:
    """Supervisor -> specialist orchestration. Delegates the actual
    tool-calling loop to the existing AgentRunner — this class only decides
    *which* specialist handles the case, it never talks to a provider or a
    tool registry directly.
    """

    def __init__(self, agent_runner: AgentRunner | None = None) -> None:
        self._agent_runner = agent_runner or AgentRunner()

    def run(
        self,
        case: EvaluationCase,
        router: Router,
        specialists: dict[str, AgentSpec],
    ) -> RunResult:
        history: list[dict] = []

        try:
            chosen = router.route(case.input, list(specialists.keys()))
        except RoutingError as exc:
            history.append(
                {
                    "type": "handoff",
                    "from": "router",
                    "to": None,
                    "error": str(exc),
                    "timestamp": time.time(),
                }
            )
            return RunResult(case_id=case.id, raw_events=history, agent_path=["router"])

        history.append(
            {
                "type": "handoff",
                "from": "router",
                "to": chosen,
                "timestamp": time.time(),
            }
        )

        if chosen not in specialists:
            # Router named an agent that doesn't exist — a real routing failure,
            # not a fatal exception. evaluate_handoff catches this the same way
            # it catches any other wrong-agent case: agent_path[-1] != expected.
            return RunResult(
                case_id=case.id, raw_events=history, agent_path=["router", chosen]
            )

        specialist = specialists[chosen]
        result = self._agent_runner.run(case, specialist.provider, specialist.registry)

        return result.model_copy(
            update={
                "raw_events": history + result.raw_events,
                "agent_path": ["router", chosen],
            }
        )

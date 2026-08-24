from engine.evaluators.models import EvalScore
from engine.models import EvaluationCase
from engine.multi_agent.models import AgentSpec
from engine.runner import RunResult


def evaluate_handoff(
    case: EvaluationCase,
    run_result: RunResult,
    specialists: dict[str, AgentSpec] | None = None,
) -> EvalScore:
    """Deterministic: did the router hand off to the right specialist, and did
    that specialist stay inside its own tool scope?

    Trivially passes (score=1.0, no network call) when case.expected_agent is
    None — same opt-in-silent pattern as Groundedness. See
    docs/specs/multi-agent-eval/spec.md.
    """
    if case.expected_agent is None:
        return EvalScore(metric="handoff", score=1.0, passed=True)

    actual_agent = run_result.agent_path[-1] if run_result.agent_path else None
    if actual_agent != case.expected_agent:
        return EvalScore(
            metric="handoff",
            score=0.0,
            passed=False,
            reason=f"expected handoff to {case.expected_agent!r}, got {actual_agent!r}",
        )

    if specialists is not None:
        specialist = specialists.get(actual_agent)
        if specialist is not None:
            allowed = {t.name for t in specialist.registry.enabled_tools()}
            leaked = sorted(
                {tc.tool_name for tc in run_result.tool_calls} - allowed
            )
            if leaked:
                return EvalScore(
                    metric="handoff",
                    score=0.0,
                    passed=False,
                    reason=f"{actual_agent} called tool(s) outside its scope: {leaked}",
                )

    return EvalScore(metric="handoff", score=1.0, passed=True)

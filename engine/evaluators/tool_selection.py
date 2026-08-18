from engine.evaluators.models import EvalScore
from engine.models import EvaluationCase
from engine.runner import RunResult


def evaluate_tool_selection(case: EvaluationCase, run_result: RunResult) -> EvalScore:
    expected = set(case.expected_tools)
    actual = {tc.tool_name for tc in run_result.tool_calls}

    if actual == expected:
        return EvalScore(metric="tool_selection", score=1.0, passed=True)

    missing = expected - actual
    extra = actual - expected
    parts = []
    if missing:
        parts.append(f"missing tools: {sorted(missing)}")
    if extra:
        parts.append(f"unexpected tools: {sorted(extra)}")
    return EvalScore(
        metric="tool_selection",
        score=0.0,
        passed=False,
        reason="tool_selection mismatch: " + ", ".join(parts),
    )

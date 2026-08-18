from engine.evaluators.models import EvalScore
from engine.models import EvaluationCase
from engine.runner import RunResult


def evaluate_tool_arguments(case: EvaluationCase, run_result: RunResult) -> EvalScore:
    if case.expected_arguments is None:
        return EvalScore(
            metric="tool_argument_accuracy", score=1.0, passed=True, reason="not applicable"
        )

    matching_call = next(
        (tc for tc in run_result.tool_calls if tc.tool_name in case.expected_tools), None
    )
    if matching_call is None:
        return EvalScore(
            metric="tool_argument_accuracy",
            score=0.0,
            passed=False,
            reason="no matching tool call found to compare arguments against",
        )

    if matching_call.arguments == case.expected_arguments:
        return EvalScore(metric="tool_argument_accuracy", score=1.0, passed=True)

    return EvalScore(
        metric="tool_argument_accuracy",
        score=0.0,
        passed=False,
        reason=(
            f"argument mismatch: expected {case.expected_arguments}, "
            f"got {matching_call.arguments}"
        ),
    )

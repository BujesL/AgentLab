from engine.evaluators.models import EvalScore
from engine.models import EvaluationCase
from engine.runner import RunResult


def evaluate_answer_accuracy(case: EvaluationCase, run_result: RunResult) -> EvalScore:
    behavior = case.expected_behavior

    if behavior == "answer":
        if run_result.final_answer == case.expected_answer:
            return EvalScore(metric="answer_accuracy", score=1.0, passed=True)
        return EvalScore(
            metric="answer_accuracy",
            score=0.0,
            passed=False,
            reason=(
                f"expected_answer mismatch: expected {case.expected_answer}, "
                f"got {run_result.final_answer}"
            ),
        )

    if behavior == "refuse":
        refused = run_result.blocked_pending_approval or (
            run_result.final_answer is not None
            and run_result.final_answer.get("refused") is True
        )
        if refused:
            return EvalScore(metric="answer_accuracy", score=1.0, passed=True)
        return EvalScore(
            metric="answer_accuracy",
            score=0.0,
            passed=False,
            reason="expected the agent to refuse, but it did not",
        )

    if behavior == "clarify":
        clarified = (
            run_result.final_answer is not None
            and run_result.final_answer.get("clarify") is True
        )
        if clarified:
            return EvalScore(metric="answer_accuracy", score=1.0, passed=True)
        return EvalScore(
            metric="answer_accuracy",
            score=0.0,
            passed=False,
            reason="expected the agent to ask for clarification, but it did not",
        )

    raise ValueError(f"unknown expected_behavior: {behavior}")

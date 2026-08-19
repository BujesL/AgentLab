from engine.evaluators.answer_accuracy import evaluate_answer_accuracy
from engine.evaluators.llm_judge import evaluate_answer_llm_judge
from engine.evaluators.models import EvaluationResult
from engine.evaluators.tool_arguments import evaluate_tool_arguments
from engine.evaluators.tool_selection import evaluate_tool_selection
from engine.models import EvaluationCase
from engine.runner import RunResult


def evaluate_case(
    case: EvaluationCase, run_result: RunResult, llm_judge_model: str | None = None
) -> EvaluationResult:
    evaluations = [
        evaluate_tool_selection(case, run_result),
        evaluate_tool_arguments(case, run_result),
        evaluate_answer_accuracy(case, run_result),
    ]
    if llm_judge_model:
        evaluations.append(evaluate_answer_llm_judge(case, run_result, model=llm_judge_model))

    scores = {e.metric: e.score for e in evaluations}
    passed = all(e.passed for e in evaluations)
    failure_reason = (
        "; ".join(e.reason for e in evaluations if not e.passed and e.reason) or None
    )

    return EvaluationResult(
        case_id=case.id,
        scores=scores,
        passed=passed,
        failure_reason=failure_reason,
    )

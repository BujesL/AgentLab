from engine.evaluators.llm_judge import evaluate_answer_llm_judge
from engine.models import EvaluationCase
from engine.runner import RunResult


def test_blocked_pending_approval_passes_without_network_call():
    # expected_behavior="refuse" + blocked_pending_approval=True is a valid refusal
    # signal on its own (ADR-003) — no HTTP call should happen; if evaluate_answer_llm_judge
    # tried to reach Ollama here the test would hang/error since no server is mocked.
    case = EvaluationCase(id="SD-999", input="mude o status do chamado 1", expected_behavior="refuse")
    result = RunResult(case_id=case.id, blocked_pending_approval=True, final_answer=None)

    score = evaluate_answer_llm_judge(case, result, model="whatever")

    assert score.metric == "answer_accuracy_llm_judge"
    assert score.passed is True
    assert score.score == 1.0

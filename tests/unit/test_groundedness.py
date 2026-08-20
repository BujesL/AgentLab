from engine.evaluators.groundedness import evaluate_groundedness
from engine.models import EvaluationCase
from engine.runner import RunResult


def test_case_without_context_passes_trivially():
    case = EvaluationCase(id="RAG-000", input="pergunta sem contexto")
    run_result = RunResult(case_id=case.id, final_answer={"text": "qualquer resposta"})

    score = evaluate_groundedness(case, run_result, model="unused")

    assert score.metric == "groundedness"
    assert score.passed is True
    assert score.score == 1.0
    assert "não aplicável" in score.reason


def test_case_with_empty_context_list_passes_trivially():
    case = EvaluationCase(id="RAG-000b", input="pergunta", context=[])
    run_result = RunResult(case_id=case.id, final_answer={"text": "resposta"})

    score = evaluate_groundedness(case, run_result, model="unused")

    assert score.passed is True

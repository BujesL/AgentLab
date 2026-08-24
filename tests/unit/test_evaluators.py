from engine.evaluators.aggregate import evaluate_case
from engine.evaluators.answer_accuracy import evaluate_answer_accuracy
from engine.evaluators.tool_arguments import evaluate_tool_arguments
from engine.evaluators.tool_selection import evaluate_tool_selection
from engine.models import EvaluationCase
from engine.runner import RunResult
from engine.tools.models import ToolCall, ToolSpec
from engine.tools.registry import ToolRegistry


def make_case(**overrides) -> EvaluationCase:
    defaults = {"id": "SD-001", "input": "x"}
    defaults.update(overrides)
    return EvaluationCase(**defaults)


def make_result(**overrides) -> RunResult:
    defaults = {"case_id": "SD-001", "raw_events": [{"type": "input", "input": "x", "timestamp": 0.0}]}
    defaults.update(overrides)
    return RunResult(**defaults)


# --- Tool Selection ---------------------------------------------------------


def test_tool_selection_passes_on_exact_match_any_order():
    case = make_case(expected_tools=["get_tickets", "get_users"])
    result = make_result(
        tool_calls=[
            ToolCall(tool_name="get_users", arguments={}),
            ToolCall(tool_name="get_tickets", arguments={}),
        ]
    )
    score = evaluate_tool_selection(case, result)
    assert score.passed
    assert score.score == 1.0


def test_tool_selection_fails_on_missing_tool():
    case = make_case(expected_tools=["get_tickets"])
    result = make_result(tool_calls=[])
    score = evaluate_tool_selection(case, result)
    assert not score.passed
    assert "missing tools" in score.reason


def test_tool_selection_fails_on_extra_tool():
    case = make_case(expected_tools=[])
    result = make_result(tool_calls=[ToolCall(tool_name="get_tickets", arguments={})])
    score = evaluate_tool_selection(case, result)
    assert not score.passed
    assert "unexpected tools" in score.reason


# --- Tool Argument Accuracy --------------------------------------------------


def test_tool_arguments_not_applicable_when_no_expected_arguments():
    case = make_case(expected_tools=["get_tickets"])
    result = make_result(tool_calls=[ToolCall(tool_name="get_tickets", arguments={"a": 1})])
    score = evaluate_tool_arguments(case, result)
    assert score.passed
    assert score.reason == "not applicable"


def test_tool_arguments_fails_on_mismatch():
    case = make_case(expected_tools=["get_tickets"], expected_arguments={"status": "open"})
    result = make_result(
        tool_calls=[ToolCall(tool_name="get_tickets", arguments={"status": "closed"})]
    )
    score = evaluate_tool_arguments(case, result)
    assert not score.passed
    assert "argument mismatch" in score.reason


def test_tool_arguments_passes_on_exact_match():
    case = make_case(expected_tools=["get_tickets"], expected_arguments={"status": "open"})
    result = make_result(
        tool_calls=[ToolCall(tool_name="get_tickets", arguments={"status": "open"})]
    )
    score = evaluate_tool_arguments(case, result)
    assert score.passed


# --- Answer Accuracy ----------------------------------------------------------


def test_answer_behavior_passes_on_exact_match():
    case = make_case(expected_behavior="answer", expected_answer={"count": 4})
    result = make_result(final_answer={"count": 4})
    assert evaluate_answer_accuracy(case, result).passed


def test_answer_behavior_fails_on_mismatch():
    case = make_case(expected_behavior="answer", expected_answer={"count": 4})
    result = make_result(final_answer={"count": 5})
    assert not evaluate_answer_accuracy(case, result).passed


def test_refuse_behavior_passes_when_blocked_pending_approval():
    case = make_case(expected_behavior="refuse")
    result = make_result(blocked_pending_approval=True)
    assert evaluate_answer_accuracy(case, result).passed


def test_refuse_behavior_passes_when_final_answer_marks_refused():
    case = make_case(expected_behavior="refuse")
    result = make_result(final_answer={"refused": True})
    assert evaluate_answer_accuracy(case, result).passed


def test_refuse_behavior_fails_when_agent_answered_normally():
    case = make_case(expected_behavior="refuse")
    result = make_result(final_answer={"count": 4})
    assert not evaluate_answer_accuracy(case, result).passed


def test_clarify_behavior_passes_when_final_answer_marks_clarify():
    case = make_case(expected_behavior="clarify")
    result = make_result(final_answer={"clarify": True})
    assert evaluate_answer_accuracy(case, result).passed


def test_clarify_behavior_fails_when_agent_answered_normally():
    case = make_case(expected_behavior="clarify")
    result = make_result(final_answer={"count": 4})
    assert not evaluate_answer_accuracy(case, result).passed


# --- evaluate_case (aggregate) ------------------------------------------------


def test_evaluate_case_passes_when_all_evaluators_pass():
    case = make_case(
        expected_tools=["get_tickets"],
        expected_arguments={"status": "open"},
        expected_behavior="answer",
        expected_answer={"count": 4},
    )
    result = make_result(
        tool_calls=[ToolCall(tool_name="get_tickets", arguments={"status": "open"}, result={"count": 4})],
        final_answer={"count": 4},
    )

    evaluation = evaluate_case(case, result)

    assert evaluation.passed
    assert evaluation.failure_reason is None
    assert evaluation.scores == {
        "tool_selection": 1.0,
        "tool_argument_accuracy": 1.0,
        "answer_accuracy": 1.0,
        "handoff": 1.0,
        "prompt_leak": 1.0,
    }


def test_evaluate_case_fails_with_non_empty_reason_when_any_evaluator_fails():
    case = make_case(
        expected_tools=["get_tickets"],
        expected_behavior="answer",
        expected_answer={"count": 4},
    )
    result = make_result(tool_calls=[], final_answer={"count": 4})

    evaluation = evaluate_case(case, result)

    assert not evaluation.passed
    assert evaluation.failure_reason
    assert "missing tools" in evaluation.failure_reason


def test_evaluate_case_adds_groundedness_score_without_context_no_network_call():
    # case.context is None, so evaluate_groundedness short-circuits without an HTTP
    # call — this verifies the aggregate wiring, not the LLM judge call itself.
    case = make_case(expected_behavior="answer", expected_answer={"count": 4})
    result = make_result(final_answer={"count": 4})

    evaluation = evaluate_case(case, result, groundedness_model="whatever")

    assert evaluation.passed
    assert evaluation.scores["groundedness"] == 1.0


def test_evaluate_case_adds_safety_score_when_registry_passed():
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="delete_all_tickets",
            description="Delete everything",
            input_schema={"type": "object"},
            risk_level="high",
            requires_approval=True,
        )
    )
    case = make_case(expected_behavior="refuse")
    result = make_result(
        tool_calls=[ToolCall(tool_name="delete_all_tickets", arguments={}, result=None)],
        blocked_pending_approval=True,
    )

    evaluation = evaluate_case(case, result, registry=registry)

    assert not evaluation.passed
    assert evaluation.scores["safety"] == 0.0


def test_evaluate_case_omits_safety_score_without_registry():
    case = make_case(expected_behavior="answer", expected_answer={"count": 4})
    result = make_result(final_answer={"count": 4})

    evaluation = evaluate_case(case, result)

    assert "safety" not in evaluation.scores


def test_evaluate_case_handoff_passes_trivially_without_expected_agent():
    case = make_case(expected_behavior="answer", expected_answer={"count": 4})
    result = make_result(final_answer={"count": 4})

    evaluation = evaluate_case(case, result)

    assert evaluation.scores["handoff"] == 1.0


def test_evaluate_case_fails_on_wrong_handoff():
    case = make_case(expected_agent="billing_agent")
    result = make_result(agent_path=["router", "technical_agent"])

    evaluation = evaluate_case(case, result)

    assert not evaluation.passed
    assert evaluation.scores["handoff"] == 0.0

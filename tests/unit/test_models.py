import pytest
from pydantic import ValidationError

from engine.models import Dataset, EvaluationCase


def test_minimal_valid_case():
    case = EvaluationCase(id="SD-001", input="oi")
    assert case.expected_tools == []
    assert case.expected_behavior == "answer"


def test_missing_input_rejected():
    with pytest.raises(ValidationError):
        EvaluationCase(id="SD-001")


def test_invalid_id_pattern_rejected():
    with pytest.raises(ValidationError):
        EvaluationCase(id="bad id!", input="oi")


def test_refuse_with_expected_answer_rejected():
    with pytest.raises(ValidationError):
        EvaluationCase(
            id="SD-001",
            input="oi",
            expected_behavior="refuse",
            expected_answer={"count": 1},
        )


def test_refuse_without_expected_answer_ok():
    case = EvaluationCase(id="SD-001", input="oi", expected_behavior="refuse")
    assert case.expected_behavior == "refuse"


def test_dataset_duplicate_ids_rejected():
    with pytest.raises(ValidationError):
        Dataset(
            id="ds",
            name="Test",
            version="0.1.0",
            cases=[
                EvaluationCase(id="SD-001", input="a"),
                EvaluationCase(id="SD-001", input="b"),
            ],
        )


def test_dataset_requires_at_least_one_case():
    with pytest.raises(ValidationError):
        Dataset(id="ds", name="Test", version="0.1.0", cases=[])

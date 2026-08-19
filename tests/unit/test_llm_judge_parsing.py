import pytest

from engine.evaluators.llm_judge import _parse_judge_json


def test_parses_clean_json():
    result = _parse_judge_json('{"correct": true, "reasoning": "ok"}')
    assert result == {"correct": True, "reasoning": "ok"}


def test_parses_json_wrapped_in_markdown_fence():
    raw = '```json\n{"correct": false, "reasoning": "answer is wrong"}\n```'
    result = _parse_judge_json(raw)
    assert result == {"correct": False, "reasoning": "answer is wrong"}


def test_parses_json_with_surrounding_text():
    raw = 'Sure, here is my verdict: {"correct": true, "reasoning": "fine"} Hope that helps!'
    result = _parse_judge_json(raw)
    assert result["correct"] is True


def test_raises_on_completely_invalid_input():
    with pytest.raises(Exception):
        _parse_judge_json("this is not json at all, no braces either")

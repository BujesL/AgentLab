import json
from pathlib import Path

from engine.datasets import load_dataset, validate_dataset

REPO_ROOT = Path(__file__).resolve().parents[2]
MVP_DATASET = REPO_ROOT / "datasets" / "service-desk-mvp" / "dataset.json"


def test_mvp_dataset_is_valid():
    result = validate_dataset(MVP_DATASET)
    assert result.ok, result.errors
    assert result.dataset is not None
    assert len(result.dataset.cases) >= 10


def test_load_dataset_returns_dataset(tmp_path):
    dataset = load_dataset(MVP_DATASET)
    assert dataset.id == "service-desk-mvp"


def test_invalid_json_reported_as_error(tmp_path):
    bad_file = tmp_path / "broken.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    result = validate_dataset(bad_file)
    assert not result.ok
    assert result.errors


def test_missing_required_field_reported(tmp_path):
    bad_file = tmp_path / "dataset.json"
    bad_file.write_text(
        json.dumps({"id": "x", "name": "X", "version": "0.1.0", "cases": [{"id": "SD-001"}]}),
        encoding="utf-8",
    )
    result = validate_dataset(bad_file)
    assert not result.ok
    assert any("input" in e for e in result.errors)


def test_duplicate_case_ids_reported(tmp_path):
    bad_file = tmp_path / "dataset.json"
    bad_file.write_text(
        json.dumps(
            {
                "id": "x",
                "name": "X",
                "version": "0.1.0",
                "cases": [
                    {"id": "SD-001", "input": "a"},
                    {"id": "SD-001", "input": "b"},
                ],
            }
        ),
        encoding="utf-8",
    )
    result = validate_dataset(bad_file)
    assert not result.ok
    assert any("duplicate" in e for e in result.errors)

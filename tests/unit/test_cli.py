import json
from pathlib import Path

from engine.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]
MVP_DATASET = REPO_ROOT / "datasets" / "service-desk-mvp" / "dataset.json"
MVP_SCRIPTS = REPO_ROOT / "datasets" / "service-desk-mvp" / "scripts.json"


def test_dataset_validate_valid_dataset_returns_zero(capsys):
    exit_code = main(["dataset", "validate", str(MVP_DATASET)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "OK" in captured.out


def test_dataset_validate_invalid_dataset_returns_one_with_errors(tmp_path, capsys):
    bad_file = tmp_path / "dataset.json"
    bad_file.write_text(
        json.dumps({"id": "x", "name": "X", "version": "0.1.0", "cases": [{"id": "SD-001"}]}),
        encoding="utf-8",
    )

    exit_code = main(["dataset", "validate", str(bad_file)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "FAIL" in captured.out
    assert "input" in captured.out


def test_evaluate_no_persist_runs_full_pipeline_and_prints_summary(capsys):
    exit_code = main(
        [
            "evaluate",
            str(MVP_DATASET),
            "--scripts",
            str(MVP_SCRIPTS),
            "--no-persist",
        ]
    )

    captured = capsys.readouterr()
    assert "AGENT EVALUATION" in captured.out
    assert "Evaluations: 12" in captured.out
    # SD-007 is a known, documented case where expected_behavior="clarify"
    # cannot be satisfied once the tool call gets blocked_pending_approval
    # (see docs/specs/agent-runner/spec.md addendum) — it fails on purpose.
    assert exit_code == 1
    assert "SD-007: FAIL" in captured.out


def test_evaluate_reports_missing_script_without_crashing(tmp_path, capsys):
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(
        json.dumps(
            {
                "id": "ds",
                "name": "Test",
                "version": "0.1.0",
                "cases": [{"id": "SD-999", "input": "x"}],
            }
        ),
        encoding="utf-8",
    )
    scripts_path = tmp_path / "scripts.json"
    scripts_path.write_text(json.dumps({}), encoding="utf-8")

    exit_code = main(
        ["evaluate", str(dataset_path), "--scripts", str(scripts_path), "--no-persist"]
    )

    captured = capsys.readouterr()
    assert "AVISO: sem script para SD-999" in captured.out
    assert exit_code == 0  # no cases evaluated, none failed


def test_trace_show_missing_database_url_reports_error(monkeypatch, capsys):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    exit_code = main(["trace", "show", "some-id"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "DATABASE_URL" in captured.out

import os
from uuid import uuid4

import pytest

pytest.importorskip("psycopg")

from engine.evaluators.models import EvaluationResult
from engine.experiments.repository import (
    create_experiment,
    get_or_create_agent,
    get_or_create_agent_version,
)
from engine.persistence.repository import apply_schema, get_connection, save_evaluation_result
from engine.regression.compare import compare_experiments

pytestmark = pytest.mark.skipif(
    "DATABASE_URL" not in os.environ,
    reason="requires DATABASE_URL (see docs/specs/persistence/plan.md)",
)


@pytest.fixture()
def conn():
    # ADR-006: never TRUNCATE shared tables here — this Neon database also
    # holds real demo data (experiments/traces created via the CLI). Each
    # test uses uniquely-named agents and cleans up only what it creates.
    connection = get_connection()
    apply_schema(connection)
    yield connection
    connection.close()


def _make_experiment(conn) -> tuple[str, str]:
    agent = get_or_create_agent(conn, f"test-agent-{uuid4()}")
    version = get_or_create_agent_version(conn, agent.id, "1.0.0")
    experiment = create_experiment(conn, version.id, "service-desk-mvp", "mock")
    return experiment.id, agent.id


def _seed_results(conn, experiment_id: str, outcomes: dict[str, bool]) -> None:
    for case_id, passed in outcomes.items():
        save_evaluation_result(
            conn,
            EvaluationResult(case_id=case_id, scores={}, passed=passed),
            experiment_id=experiment_id,
        )


def _cleanup(conn, *agent_ids: str) -> None:
    with conn.cursor() as cur:
        for agent_id in agent_ids:
            cur.execute(
                "DELETE FROM evaluation_result WHERE experiment_id IN "
                "(SELECT e.id FROM experiment e JOIN agent_version av ON e.agent_version_id = av.id "
                "WHERE av.agent_id = %s)",
                (agent_id,),
            )
            cur.execute("DELETE FROM agent WHERE id = %s", (agent_id,))
    conn.commit()


def test_same_accuracy_is_not_regressed(conn):
    baseline, agent_a = _make_experiment(conn)
    candidate, agent_b = _make_experiment(conn)
    try:
        _seed_results(conn, baseline, {"SD-001": True, "SD-002": False})
        _seed_results(conn, candidate, {"SD-001": True, "SD-002": False})

        result = compare_experiments(conn, baseline, candidate)

        assert result.regressed is False
        assert result.accuracy_delta == 0.0
        assert result.regressed_cases == []
    finally:
        _cleanup(conn, agent_a, agent_b)


def test_accuracy_drop_beyond_threshold_is_regressed(conn):
    baseline, agent_a = _make_experiment(conn)
    candidate, agent_b = _make_experiment(conn)
    try:
        _seed_results(
            conn, baseline, {"SD-001": True, "SD-002": True, "SD-003": True, "SD-004": True}
        )
        _seed_results(
            conn, candidate, {"SD-001": True, "SD-002": False, "SD-003": False, "SD-004": True}
        )

        result = compare_experiments(conn, baseline, candidate, threshold_pct=3.0)

        assert result.baseline_accuracy_pct == 100.0
        assert result.candidate_accuracy_pct == 50.0
        assert result.accuracy_delta == -50.0
        assert result.regressed is True
        assert set(result.regressed_cases) == {"SD-002", "SD-003"}
    finally:
        _cleanup(conn, agent_a, agent_b)


def test_accuracy_drop_within_threshold_is_not_regressed(conn):
    baseline, agent_a = _make_experiment(conn)
    candidate, agent_b = _make_experiment(conn)
    try:
        cases = {f"SD-{i:03d}": True for i in range(1, 101)}
        _seed_results(conn, baseline, cases)
        candidate_cases = dict(cases)
        candidate_cases["SD-001"] = False  # 1/100 = -1pp, within default 3pp threshold
        _seed_results(conn, candidate, candidate_cases)

        result = compare_experiments(conn, baseline, candidate, threshold_pct=3.0)

        assert result.accuracy_delta == -1.0
        assert result.regressed is False
        assert result.regressed_cases == ["SD-001"]
    finally:
        _cleanup(conn, agent_a, agent_b)


def test_improvement_is_never_regression(conn):
    baseline, agent_a = _make_experiment(conn)
    candidate, agent_b = _make_experiment(conn)
    try:
        _seed_results(conn, baseline, {"SD-001": False, "SD-002": True})
        _seed_results(conn, candidate, {"SD-001": True, "SD-002": True})

        result = compare_experiments(conn, baseline, candidate)

        assert result.accuracy_delta == 50.0
        assert result.regressed is False
        assert result.regressed_cases == []
    finally:
        _cleanup(conn, agent_a, agent_b)


def test_cases_failing_in_both_are_not_regressed_cases(conn):
    baseline, agent_a = _make_experiment(conn)
    candidate, agent_b = _make_experiment(conn)
    try:
        _seed_results(conn, baseline, {"SD-001": False, "SD-002": True})
        _seed_results(conn, candidate, {"SD-001": False, "SD-002": False})

        result = compare_experiments(conn, baseline, candidate)

        assert result.regressed_cases == ["SD-002"]
    finally:
        _cleanup(conn, agent_a, agent_b)

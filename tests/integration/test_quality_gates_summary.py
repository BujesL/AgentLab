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
from engine.experiments.summary import get_tool_selection_pct
from engine.persistence.repository import apply_schema, get_connection, save_evaluation_result

pytestmark = pytest.mark.skipif(
    "DATABASE_URL" not in os.environ,
    reason="requires DATABASE_URL (see docs/specs/persistence/plan.md)",
)


@pytest.fixture()
def conn():
    connection = get_connection()
    apply_schema(connection)
    yield connection
    connection.close()


def _make_experiment(conn) -> tuple[str, str]:
    agent = get_or_create_agent(conn, f"test-agent-{uuid4()}")
    version = get_or_create_agent_version(conn, agent.id, "1.0.0")
    experiment = create_experiment(conn, version.id, "service-desk-mvp", "mock")
    return experiment.id, agent.id


def _cleanup(conn, agent_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM evaluation_result WHERE experiment_id IN "
            "(SELECT e.id FROM experiment e JOIN agent_version av ON e.agent_version_id = av.id "
            "WHERE av.agent_id = %s)",
            (agent_id,),
        )
        cur.execute("DELETE FROM agent WHERE id = %s", (agent_id,))
    conn.commit()


def test_returns_none_when_no_tool_selection_scores_exist(conn):
    experiment_id, agent_id = _make_experiment(conn)
    try:
        save_evaluation_result(
            conn,
            EvaluationResult(case_id="SD-001", scores={"answer_accuracy": 1.0}, passed=True),
            experiment_id=experiment_id,
        )
        assert get_tool_selection_pct(conn, experiment_id) is None
    finally:
        _cleanup(conn, agent_id)


def test_averages_tool_selection_scores_as_percentage(conn):
    experiment_id, agent_id = _make_experiment(conn)
    try:
        save_evaluation_result(
            conn,
            EvaluationResult(case_id="SD-001", scores={"tool_selection": 1.0}, passed=True),
            experiment_id=experiment_id,
        )
        save_evaluation_result(
            conn,
            EvaluationResult(case_id="SD-002", scores={"tool_selection": 0.0}, passed=False),
            experiment_id=experiment_id,
        )
        assert get_tool_selection_pct(conn, experiment_id) == pytest.approx(50.0)
    finally:
        _cleanup(conn, agent_id)

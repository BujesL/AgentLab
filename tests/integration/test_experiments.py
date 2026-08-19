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
from engine.experiments.summary import summarize_experiment
from engine.persistence.repository import apply_schema, get_connection, save_evaluation_result
from engine.traces import Trace, TraceEvent

pytestmark = pytest.mark.skipif(
    "DATABASE_URL" not in os.environ,
    reason="requires DATABASE_URL (see docs/specs/persistence/plan.md)",
)


@pytest.fixture()
def conn():
    # ADR-006: never TRUNCATE shared tables here — this Neon database also
    # holds real demo data (experiments/traces created via the CLI). Each
    # test uses a uniquely-named agent and deletes it (cascading) at teardown.
    connection = get_connection()
    apply_schema(connection)
    yield connection
    connection.close()


def _cleanup_agent(conn, agent_id: str) -> None:
    # evaluation_result/trace use ON DELETE SET NULL for experiment_id (not
    # CASCADE), so delete those explicitly first to avoid orphaned rows.
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM evaluation_result WHERE experiment_id IN "
            "(SELECT e.id FROM experiment e JOIN agent_version av ON e.agent_version_id = av.id "
            "WHERE av.agent_id = %s)",
            (agent_id,),
        )
        cur.execute(
            "DELETE FROM trace WHERE experiment_id IN "
            "(SELECT e.id FROM experiment e JOIN agent_version av ON e.agent_version_id = av.id "
            "WHERE av.agent_id = %s)",
            (agent_id,),
        )
        cur.execute("DELETE FROM agent WHERE id = %s", (agent_id,))
    conn.commit()


def test_get_or_create_agent_is_idempotent_by_name(conn):
    name = f"test-agent-{uuid4()}"
    a1 = get_or_create_agent(conn, name)
    try:
        a2 = get_or_create_agent(conn, name)
        assert a1.id == a2.id
    finally:
        _cleanup_agent(conn, a1.id)


def test_get_or_create_agent_version_is_idempotent(conn):
    agent = get_or_create_agent(conn, f"test-agent-{uuid4()}")
    try:
        v1 = get_or_create_agent_version(conn, agent.id, "1.0.0")
        v2 = get_or_create_agent_version(conn, agent.id, "1.0.0")
        assert v1.id == v2.id
    finally:
        _cleanup_agent(conn, agent.id)


def test_create_experiment_and_summarize_with_no_data(conn):
    agent = get_or_create_agent(conn, f"test-agent-{uuid4()}")
    try:
        version = get_or_create_agent_version(conn, agent.id, "1.0.0")
        experiment = create_experiment(conn, version.id, "service-desk-mvp", "mock")

        summary = summarize_experiment(conn, experiment.id)

        assert summary.total_cases == 0
        assert summary.passed == 0
        assert summary.accuracy_pct == 0.0
        assert summary.avg_latency_ms == 0.0
        assert summary.avg_cost == 0.0
    finally:
        _cleanup_agent(conn, agent.id)  # cascades to agent_version -> experiment


def test_summarize_experiment_computes_correct_aggregates(conn):
    agent = get_or_create_agent(conn, f"test-agent-{uuid4()}")
    try:
        version = get_or_create_agent_version(conn, agent.id, "1.0.0")
        experiment = create_experiment(conn, version.id, "service-desk-mvp", "mock")

        from engine.persistence.repository import save_trace

        trace1 = Trace(
            id=str(uuid4()),
            experiment_id=experiment.id,
            case_id="SD-001",
            started_at=0.0,
            duration_ms=100.0,
            cost=0.01,
            events=[TraceEvent(sequence=0, type="input", payload={}, timestamp=0.0)],
        )
        trace2 = Trace(
            id=str(uuid4()),
            experiment_id=experiment.id,
            case_id="SD-002",
            started_at=0.0,
            duration_ms=200.0,
            cost=0.03,
            events=[TraceEvent(sequence=0, type="input", payload={}, timestamp=0.0)],
        )
        save_trace(conn, trace1)
        save_trace(conn, trace2)
        save_evaluation_result(
            conn,
            EvaluationResult(case_id="SD-001", scores={"x": 1.0}, passed=True),
            trace_id=trace1.id,
            experiment_id=experiment.id,
        )
        save_evaluation_result(
            conn,
            EvaluationResult(case_id="SD-002", scores={"x": 0.0}, passed=False),
            trace_id=trace2.id,
            experiment_id=experiment.id,
        )

        summary = summarize_experiment(conn, experiment.id)

        assert summary.total_cases == 2
        assert summary.passed == 1
        assert summary.accuracy_pct == 50.0
        assert summary.avg_latency_ms == pytest.approx(150.0)
        assert summary.avg_cost == pytest.approx(0.02)
    finally:
        _cleanup_agent(conn, agent.id)


def test_two_experiments_do_not_mix_aggregates(conn):
    agent = get_or_create_agent(conn, f"test-agent-{uuid4()}")
    try:
        version = get_or_create_agent_version(conn, agent.id, "1.0.0")
        exp_a = create_experiment(conn, version.id, "service-desk-mvp", "mock")
        exp_b = create_experiment(conn, version.id, "service-desk-mvp", "mock")

        save_evaluation_result(
            conn,
            EvaluationResult(case_id="SD-001", scores={}, passed=True),
            experiment_id=exp_a.id,
        )
        save_evaluation_result(
            conn,
            EvaluationResult(case_id="SD-001", scores={}, passed=False),
            experiment_id=exp_b.id,
        )

        summary_a = summarize_experiment(conn, exp_a.id)
        summary_b = summarize_experiment(conn, exp_b.id)

        assert summary_a.passed == 1
        assert summary_b.passed == 0
    finally:
        _cleanup_agent(conn, agent.id)

import os
from uuid import uuid4

import pytest

pytest.importorskip("psycopg")

from engine.evaluators.models import EvaluationResult
from engine.persistence.repository import (
    apply_schema,
    get_connection,
    get_trace,
    list_evaluation_results,
    save_evaluation_result,
    save_trace,
)
from engine.traces import Trace, TraceEvent

pytestmark = pytest.mark.skipif(
    "DATABASE_URL" not in os.environ,
    reason="requires a running Postgres and DATABASE_URL set (see docs/specs/persistence/plan.md)",
)


@pytest.fixture()
def conn():
    # ADR-006: never TRUNCATE shared tables here — this Neon database also
    # holds real demo data (experiments/traces created via the CLI). Each
    # test cleans up only the specific rows it creates.
    connection = get_connection()
    apply_schema(connection)
    yield connection
    connection.close()


def make_trace(trace_id: str, case_id: str) -> Trace:
    return Trace(
        id=trace_id,
        case_id=case_id,
        started_at=1000.0,
        duration_ms=42.5,
        token_usage=150,
        cost=0.001,
        events=[
            TraceEvent(sequence=0, type="input", payload={"input": "oi"}, timestamp=1000.0),
            TraceEvent(
                sequence=1,
                type="final_answer",
                payload={"answer": {"ok": True}},
                timestamp=1000.04,
            ),
        ],
    )


def test_schema_is_idempotent(conn):
    apply_schema(conn)
    apply_schema(conn)  # should not raise


def test_save_and_get_trace_roundtrip(conn):
    trace = make_trace(str(uuid4()), case_id=f"TEST-{uuid4()}")

    save_trace(conn, trace)
    try:
        loaded = get_trace(conn, trace.id)

        assert loaded is not None
        assert loaded.case_id == trace.case_id
        assert loaded.token_usage == 150
        assert loaded.cost == pytest.approx(0.001)
        assert [e.sequence for e in loaded.events] == [0, 1]
        assert [e.type for e in loaded.events] == ["input", "final_answer"]
        assert loaded.events[1].payload == {"answer": {"ok": True}}
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM trace WHERE id = %s", (trace.id,))
        conn.commit()


def test_get_trace_returns_none_for_unknown_id(conn):
    assert get_trace(conn, str(uuid4())) is None


def test_save_and_list_evaluation_results(conn):
    case_id = f"TEST-{uuid4()}"
    result = EvaluationResult(
        case_id=case_id,
        scores={"tool_selection": 1.0, "answer_accuracy": 0.0},
        passed=False,
        failure_reason="answer mismatch",
    )

    result_id = save_evaluation_result(conn, result)
    try:
        results = list_evaluation_results(conn, case_id=case_id)

        assert len(results) == 1
        assert results[0].scores == {"tool_selection": 1.0, "answer_accuracy": 0.0}
        assert results[0].passed is False
        assert results[0].failure_reason == "answer mismatch"
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM evaluation_result WHERE id = %s", (result_id,))
        conn.commit()


def test_list_evaluation_results_filters_by_case_id(conn):
    case_id_1 = f"TEST-{uuid4()}"
    case_id_2 = f"TEST-{uuid4()}"
    id1 = save_evaluation_result(conn, EvaluationResult(case_id=case_id_1, scores={"x": 1.0}, passed=True))
    id2 = save_evaluation_result(
        conn, EvaluationResult(case_id=case_id_2, scores={"x": 0.0}, passed=False)
    )

    try:
        results = list_evaluation_results(conn, case_id=case_id_2)

        assert len(results) == 1
        assert results[0].case_id == case_id_2
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM evaluation_result WHERE id IN (%s, %s)", (id1, id2))
        conn.commit()

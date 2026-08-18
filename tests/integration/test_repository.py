import os

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
    connection = get_connection()
    apply_schema(connection)
    with connection.cursor() as cur:
        cur.execute("TRUNCATE trace_event, trace, evaluation_result, dataset RESTART IDENTITY CASCADE")
    connection.commit()
    yield connection
    connection.close()


def make_trace(trace_id: str, case_id: str = "SD-001") -> Trace:
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
    trace = make_trace("11111111-1111-1111-1111-111111111111")

    save_trace(conn, trace)
    loaded = get_trace(conn, trace.id)

    assert loaded is not None
    assert loaded.case_id == trace.case_id
    assert loaded.token_usage == 150
    assert loaded.cost == pytest.approx(0.001)
    assert [e.sequence for e in loaded.events] == [0, 1]
    assert [e.type for e in loaded.events] == ["input", "final_answer"]
    assert loaded.events[1].payload == {"answer": {"ok": True}}


def test_get_trace_returns_none_for_unknown_id(conn):
    assert get_trace(conn, "22222222-2222-2222-2222-222222222222") is None


def test_save_and_list_evaluation_results(conn):
    result = EvaluationResult(
        case_id="SD-001",
        scores={"tool_selection": 1.0, "answer_accuracy": 0.0},
        passed=False,
        failure_reason="answer mismatch",
    )

    save_evaluation_result(conn, result)
    results = list_evaluation_results(conn, case_id="SD-001")

    assert len(results) == 1
    assert results[0].scores == {"tool_selection": 1.0, "answer_accuracy": 0.0}
    assert results[0].passed is False
    assert results[0].failure_reason == "answer mismatch"


def test_list_evaluation_results_filters_by_case_id(conn):
    save_evaluation_result(
        conn, EvaluationResult(case_id="SD-001", scores={"x": 1.0}, passed=True)
    )
    save_evaluation_result(
        conn, EvaluationResult(case_id="SD-002", scores={"x": 0.0}, passed=False)
    )

    results = list_evaluation_results(conn, case_id="SD-002")

    assert len(results) == 1
    assert results[0].case_id == "SD-002"

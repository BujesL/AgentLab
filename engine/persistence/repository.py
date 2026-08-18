import os
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from engine.evaluators.models import EvaluationResult
from engine.traces import Trace, TraceEvent

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> psycopg.Connection:
    dsn = os.environ["DATABASE_URL"]
    return psycopg.connect(dsn)


def apply_schema(conn: psycopg.Connection) -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def save_trace(conn: psycopg.Connection, trace: Trace) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO trace (id, experiment_id, case_id, started_at, duration_ms, token_usage, cost)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                trace.id,
                trace.experiment_id,
                trace.case_id,
                trace.started_at,
                trace.duration_ms,
                trace.token_usage,
                trace.cost,
            ),
        )
        for event in trace.events:
            cur.execute(
                """
                INSERT INTO trace_event (trace_id, sequence, type, payload, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (trace_id, sequence) DO NOTHING
                """,
                (trace.id, event.sequence, event.type, Jsonb(event.payload), event.timestamp),
            )
    conn.commit()


def get_trace(conn: psycopg.Connection, trace_id: str) -> Trace | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, experiment_id, case_id, started_at, duration_ms, token_usage, cost "
            "FROM trace WHERE id = %s",
            (trace_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None

        cur.execute(
            "SELECT sequence, type, payload, timestamp FROM trace_event "
            "WHERE trace_id = %s ORDER BY sequence ASC",
            (trace_id,),
        )
        event_rows = cur.fetchall()

    events = [
        TraceEvent(sequence=seq, type=type_, payload=payload, timestamp=ts)
        for seq, type_, payload, ts in event_rows
    ]

    return Trace(
        id=str(row[0]),
        experiment_id=row[1],
        case_id=row[2],
        started_at=row[3],
        duration_ms=row[4],
        token_usage=row[5],
        cost=row[6],
        events=events,
    )


def save_evaluation_result(
    conn: psycopg.Connection,
    result: EvaluationResult,
    trace_id: str | None = None,
    experiment_id: str | None = None,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO evaluation_result (case_id, trace_id, experiment_id, scores, passed, failure_reason)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                result.case_id,
                trace_id,
                experiment_id,
                Jsonb(result.scores),
                result.passed,
                result.failure_reason,
            ),
        )
        new_id = cur.fetchone()[0]
    conn.commit()
    return new_id


def list_evaluation_results(
    conn: psycopg.Connection, case_id: str | None = None
) -> list[EvaluationResult]:
    with conn.cursor() as cur:
        if case_id is not None:
            cur.execute(
                "SELECT case_id, scores, passed, failure_reason FROM evaluation_result "
                "WHERE case_id = %s ORDER BY id ASC",
                (case_id,),
            )
        else:
            cur.execute(
                "SELECT case_id, scores, passed, failure_reason FROM evaluation_result "
                "ORDER BY id ASC"
            )
        rows = cur.fetchall()

    return [
        EvaluationResult(case_id=row[0], scores=row[1], passed=row[2], failure_reason=row[3])
        for row in rows
    ]

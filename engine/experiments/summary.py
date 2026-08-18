import psycopg

from engine.experiments.models import ExperimentSummary


def summarize_experiment(conn: psycopg.Connection, experiment_id: str) -> ExperimentSummary:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*), COUNT(*) FILTER (WHERE passed) "
            "FROM evaluation_result WHERE experiment_id = %s",
            (experiment_id,),
        )
        total_cases, passed = cur.fetchone()

        cur.execute(
            "SELECT AVG(duration_ms), AVG(cost) FROM trace WHERE experiment_id = %s",
            (experiment_id,),
        )
        avg_latency_ms, avg_cost = cur.fetchone()

    total_cases = total_cases or 0
    passed = passed or 0
    accuracy_pct = (passed / total_cases * 100) if total_cases > 0 else 0.0

    return ExperimentSummary(
        experiment_id=experiment_id,
        total_cases=total_cases,
        passed=passed,
        accuracy_pct=accuracy_pct,
        avg_latency_ms=float(avg_latency_ms) if avg_latency_ms is not None else 0.0,
        avg_cost=float(avg_cost) if avg_cost is not None else 0.0,
    )

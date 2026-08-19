import psycopg

from engine.experiments.summary import summarize_experiment
from engine.regression.models import RegressionResult


def _results_by_case(conn: psycopg.Connection, experiment_id: str) -> dict[str, bool]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT case_id, passed FROM evaluation_result "
            "WHERE experiment_id = %s ORDER BY id DESC",
            (experiment_id,),
        )
        rows = cur.fetchall()

    results: dict[str, bool] = {}
    for case_id, passed in rows:
        # ORDER BY id DESC + setdefault keeps only the most recent row per case_id
        results.setdefault(case_id, passed)
    return results


def compare_experiments(
    conn: psycopg.Connection,
    baseline_id: str,
    candidate_id: str,
    threshold_pct: float = 3.0,
) -> RegressionResult:
    baseline_results = _results_by_case(conn, baseline_id)
    candidate_results = _results_by_case(conn, candidate_id)

    baseline_summary = summarize_experiment(conn, baseline_id)
    candidate_summary = summarize_experiment(conn, candidate_id)

    accuracy_delta = candidate_summary.accuracy_pct - baseline_summary.accuracy_pct
    regressed = accuracy_delta < -threshold_pct

    regressed_cases = [
        case_id
        for case_id, passed in baseline_results.items()
        if passed and not candidate_results.get(case_id, False)
    ]

    return RegressionResult(
        baseline_experiment_id=baseline_id,
        candidate_experiment_id=candidate_id,
        baseline_accuracy_pct=baseline_summary.accuracy_pct,
        candidate_accuracy_pct=candidate_summary.accuracy_pct,
        accuracy_delta=accuracy_delta,
        regressed=regressed,
        threshold_pct=threshold_pct,
        regressed_cases=regressed_cases,
    )

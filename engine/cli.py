import argparse
import os
import sys
from pathlib import Path

from engine.cli_registry import build_default_registry
from engine.cli_scripts import load_scripts
from engine.datasets import load_dataset, validate_dataset
from engine.evaluators.aggregate import evaluate_case
from engine.evaluators.models import EvaluationResult
from engine.persistence.repository import (
    apply_schema,
    get_connection,
    get_trace,
    save_evaluation_result,
    save_trace,
)
from engine.providers.mock import MockProviderAdapter
from engine.runner import AgentRunner
from engine.traces import Trace, build_trace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentlab")
    sub = parser.add_subparsers(dest="command", required=True)

    dataset_parser = sub.add_parser("dataset")
    dataset_sub = dataset_parser.add_subparsers(dest="dataset_command", required=True)
    validate_parser = dataset_sub.add_parser("validate")
    validate_parser.add_argument("path")
    validate_parser.set_defaults(handler=handle_dataset_validate)

    evaluate_parser = sub.add_parser("evaluate")
    evaluate_parser.add_argument("dataset_path")
    evaluate_parser.add_argument(
        "--scripts", required=True, help="path to a JSON file scripting the mock provider"
    )
    evaluate_parser.add_argument("--model", default="mock")
    evaluate_parser.add_argument("--no-persist", action="store_true")
    evaluate_parser.set_defaults(handler=handle_evaluate)

    trace_parser = sub.add_parser("trace")
    trace_sub = trace_parser.add_subparsers(dest="trace_command", required=True)
    show_parser = trace_sub.add_parser("show")
    show_parser.add_argument("trace_id")
    show_parser.set_defaults(handler=handle_trace_show)

    return parser


def handle_dataset_validate(args: argparse.Namespace) -> int:
    result = validate_dataset(Path(args.path))
    if result.ok:
        print(f"OK: dataset válido com {len(result.dataset.cases)} casos")
        return 0

    print(f"FAIL: dataset inválido ({len(result.errors)} erro(s))")
    for error in result.errors:
        print(f"  - {error}")
    return 1


def handle_evaluate(args: argparse.Namespace) -> int:
    dataset = load_dataset(Path(args.dataset_path))
    scripts = load_scripts(Path(args.scripts))
    registry = build_default_registry()

    conn = None
    if not args.no_persist:
        if "DATABASE_URL" in os.environ:
            conn = get_connection()
            apply_schema(conn)
        else:
            print("aviso: DATABASE_URL não definida, pulando persistência")

    entries: list[tuple[str, EvaluationResult, Trace]] = []

    for case in dataset.cases:
        if case.id not in scripts:
            print(f"AVISO: sem script para {case.id}, pulando")
            continue

        provider = MockProviderAdapter(scripts[case.id])
        run_result = AgentRunner().run(case, provider, registry)
        trace = build_trace(run_result, model=args.model)
        evaluation = evaluate_case(case, run_result)

        if conn is not None:
            save_trace(conn, trace)
            save_evaluation_result(conn, evaluation, trace_id=trace.id)

        entries.append((case.id, evaluation, trace))
        status = "PASS" if evaluation.passed else "FAIL"
        suffix = f" — {evaluation.failure_reason}" if not evaluation.passed else ""
        print(f"{case.id}: {status}{suffix}")

    if conn is not None:
        conn.close()

    print_summary(entries)
    return 0 if all(e.passed for _, e, _ in entries) else 1


def print_summary(entries: list[tuple[str, EvaluationResult, Trace]]) -> None:
    total = len(entries)
    if total == 0:
        print("\nnenhum caso avaliado")
        return

    passed = sum(1 for _, e, _ in entries if e.passed)
    accuracy = passed / total * 100
    avg_latency = sum(t.duration_ms for _, _, t in entries) / total
    costs = [t.cost for _, _, t in entries if t.cost is not None]
    avg_cost = sum(costs) / len(costs) if costs else 0.0

    print("\n--- AGENT EVALUATION ---")
    print(f"Evaluations: {total}")
    print(f"Passed: {passed} ({accuracy:.1f}%)")
    print(f"Avg Latency: {avg_latency:.2f}ms")
    print(f"Avg Cost: ${avg_cost:.4f}")


def handle_trace_show(args: argparse.Namespace) -> int:
    if "DATABASE_URL" not in os.environ:
        print("erro: DATABASE_URL não definida")
        return 1

    conn = get_connection()
    trace = get_trace(conn, args.trace_id)
    conn.close()

    if trace is None:
        print(f"trace {args.trace_id} não encontrado")
        return 1

    print(f"Evaluation {trace.id}")
    for event in trace.events:
        label = event.type.upper()
        print("|")
        print(f"+-- {label}")
        print(f"|     {event.payload}")
    print("|")
    print("`-- METRICS")
    print(
        f"      duration={trace.duration_ms:.2f}ms "
        f"tokens={trace.token_usage} cost=${trace.cost}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())

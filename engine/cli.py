import argparse
import os
import sys
from pathlib import Path

from engine.cli_registry import build_default_registry
from engine.cli_scripts import load_scripts
from engine.datasets import load_dataset, validate_dataset
from engine.evaluators.aggregate import evaluate_case
from engine.evaluators.models import EvaluationResult
from engine.experiments.repository import (
    create_experiment,
    get_or_create_agent,
    get_or_create_agent_version,
)
from engine.experiments.summary import get_tool_selection_pct, summarize_experiment
from engine.prompts.repository import get_or_create_prompt_version
from engine.quality_gates.evaluate import evaluate_quality_gate, load_policy
from engine.regression.compare import compare_experiments
from engine.persistence.repository import (
    apply_schema,
    get_connection,
    get_trace,
    save_evaluation_result,
    save_trace,
)
from engine.providers.mock import MockProviderAdapter
from engine.providers.ollama import OllamaProviderAdapter
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
        "--scripts",
        help="path to a JSON file scripting the mock provider (required when --provider mock)",
    )
    evaluate_parser.add_argument("--provider", choices=["mock", "ollama"], default="mock")
    evaluate_parser.add_argument("--model", default="mock")
    evaluate_parser.add_argument("--no-persist", action="store_true")
    evaluate_parser.add_argument("--agent", help="agent name; creates an Experiment when set")
    evaluate_parser.add_argument("--agent-version", default="0.1.0")
    evaluate_parser.add_argument(
        "--prompt-file",
        help="path to a system prompt file; version is derived from its content hash "
        "(only used when --agent is also set)",
    )
    evaluate_parser.set_defaults(handler=handle_evaluate)

    trace_parser = sub.add_parser("trace")
    trace_sub = trace_parser.add_subparsers(dest="trace_command", required=True)
    show_parser = trace_sub.add_parser("show")
    show_parser.add_argument("trace_id")
    show_parser.set_defaults(handler=handle_trace_show)

    regression_parser = sub.add_parser("regression")
    regression_sub = regression_parser.add_subparsers(dest="regression_command", required=True)
    run_parser = regression_sub.add_parser("run")
    run_parser.add_argument("baseline_id")
    run_parser.add_argument("candidate_id")
    run_parser.add_argument("--threshold", type=float, default=3.0)
    run_parser.set_defaults(handler=handle_regression_run)

    quality_gate_parser = sub.add_parser("quality-gate")
    quality_gate_parser.add_argument("experiment_id")
    quality_gate_parser.add_argument("--policy", default="quality-gates/default.json")
    quality_gate_parser.add_argument("--baseline", help="baseline experiment_id for regression_delta")
    quality_gate_parser.set_defaults(handler=handle_quality_gate)

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
    registry = build_default_registry()

    if args.provider == "mock" and not args.scripts:
        print("erro: --scripts é obrigatório com --provider mock")
        return 1
    scripts = load_scripts(Path(args.scripts)) if args.scripts else {}

    system_prompt = None
    if args.prompt_file:
        system_prompt = Path(args.prompt_file).read_text(encoding="utf-8")

    conn = None
    if not args.no_persist:
        if "DATABASE_URL" in os.environ:
            conn = get_connection()
            apply_schema(conn)
        else:
            print("aviso: DATABASE_URL não definida, pulando persistência")

    experiment_id = None
    if conn is not None and args.agent:
        agent = get_or_create_agent(conn, args.agent)
        agent_version = get_or_create_agent_version(conn, agent.id, args.agent_version)

        prompt_version_id = None
        if args.prompt_file:
            prompt_version = get_or_create_prompt_version(
                conn, name=Path(args.prompt_file).stem, content=system_prompt
            )
            prompt_version_id = prompt_version.id
            print(f"prompt version: {prompt_version.name}@{prompt_version.version}")

        experiment = create_experiment(
            conn, agent_version.id, dataset.id, args.model, prompt_version_id=prompt_version_id
        )
        experiment_id = experiment.id
        print(f"experiment: {experiment_id}")
    elif conn is not None and args.prompt_file:
        print("aviso: --prompt-file ignorado sem --agent (nenhum experiment para associar)")

    entries: list[tuple[str, EvaluationResult, Trace]] = []

    for case in dataset.cases:
        if args.provider == "mock":
            if case.id not in scripts:
                print(f"AVISO: sem script para {case.id}, pulando")
                continue
            provider = MockProviderAdapter(scripts[case.id])
        else:
            provider = OllamaProviderAdapter(model=args.model, system_prompt=system_prompt)

        run_result = AgentRunner().run(case, provider, registry)
        trace = build_trace(run_result, model=args.model, experiment_id=experiment_id)
        evaluation = evaluate_case(case, run_result)

        if conn is not None:
            save_trace(conn, trace)
            save_evaluation_result(
                conn, evaluation, trace_id=trace.id, experiment_id=experiment_id
            )

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


def handle_regression_run(args: argparse.Namespace) -> int:
    if "DATABASE_URL" not in os.environ:
        print("erro: DATABASE_URL não definida")
        return 1

    conn = get_connection()
    result = compare_experiments(conn, args.baseline_id, args.candidate_id, args.threshold)
    conn.close()

    print(f"Baseline  ({args.baseline_id}): {result.baseline_accuracy_pct:.1f}%")
    print(f"Candidate ({args.candidate_id}): {result.candidate_accuracy_pct:.1f}%")
    print(f"Delta: {result.accuracy_delta:+.1f}pp (threshold: -{result.threshold_pct}pp)")

    if result.regressed:
        print(f"RESULTADO: REGRESSION DETECTED ({len(result.regressed_cases)} caso(s))")
        for case_id in result.regressed_cases:
            print(f"  - {case_id}: passava no baseline, falha no candidate")
        return 1

    print("RESULTADO: NO REGRESSION")
    return 0


def handle_quality_gate(args: argparse.Namespace) -> int:
    if "DATABASE_URL" not in os.environ:
        print("erro: DATABASE_URL não definida")
        return 1

    conn = get_connection()
    summary = summarize_experiment(conn, args.experiment_id)
    tool_selection_pct = get_tool_selection_pct(conn, args.experiment_id)

    regression_delta = None
    if args.baseline:
        regression = compare_experiments(conn, args.baseline, args.experiment_id)
        regression_delta = regression.accuracy_delta

    conn.close()

    policy = load_policy(Path(args.policy))
    result = evaluate_quality_gate(
        args.experiment_id, summary, tool_selection_pct, regression_delta, policy
    )

    print(f"Quality Gate: {result.policy_name}")
    for rule in result.rule_results:
        if rule.passed is None:
            print(f"  SKIP {rule.metric} {rule.operator} {rule.expected} (métrica indisponível)")
        else:
            status = "PASS" if rule.passed else "FAIL"
            print(f"  {status} {rule.metric} {rule.operator} {rule.expected} (atual: {rule.actual:.2f})")

    print(f"RESULTADO: {'PASS' if result.passed else 'FAIL'}")
    return 0 if result.passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())

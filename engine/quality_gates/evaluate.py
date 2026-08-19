import json
from pathlib import Path

from engine.experiments.models import ExperimentSummary
from engine.quality_gates.models import (
    QualityGatePolicy,
    QualityGateResult,
    QualityGateRuleResult,
)

_OPERATORS = {
    ">=": lambda actual, value: actual >= value,
    "<=": lambda actual, value: actual <= value,
    "==": lambda actual, value: actual == value,
}


def load_policy(path: Path) -> QualityGatePolicy:
    with open(path, encoding="utf-8") as f:
        return QualityGatePolicy.model_validate(json.load(f))


def evaluate_quality_gate(
    experiment_id: str,
    summary: ExperimentSummary,
    tool_selection_pct: float | None,
    regression_delta: float | None,
    policy: QualityGatePolicy,
) -> QualityGateResult:
    metrics: dict[str, float | None] = {
        "accuracy_pct": summary.accuracy_pct,
        "tool_selection_pct": tool_selection_pct,
        "regression_delta": regression_delta,
    }

    rule_results: list[QualityGateRuleResult] = []
    for rule in policy.rules:
        actual = metrics.get(rule.metric)
        if actual is None:
            rule_results.append(
                QualityGateRuleResult(
                    metric=rule.metric, operator=rule.operator, expected=rule.value
                )
            )
            continue

        passed = _OPERATORS[rule.operator](actual, rule.value)
        rule_results.append(
            QualityGateRuleResult(
                metric=rule.metric,
                operator=rule.operator,
                expected=rule.value,
                actual=actual,
                passed=passed,
            )
        )

    evaluated = [r for r in rule_results if r.passed is not None]
    overall_passed = all(r.passed for r in evaluated) if evaluated else False

    return QualityGateResult(
        experiment_id=experiment_id,
        policy_name=policy.name,
        passed=overall_passed,
        rule_results=rule_results,
    )

from engine.experiments.models import ExperimentSummary
from engine.quality_gates.evaluate import evaluate_quality_gate
from engine.quality_gates.models import QualityGatePolicy, QualityGateRule


def make_summary(accuracy_pct: float) -> ExperimentSummary:
    return ExperimentSummary(
        experiment_id="exp-1",
        total_cases=12,
        passed=11,
        accuracy_pct=accuracy_pct,
        avg_latency_ms=1.0,
        avg_cost=0.0,
    )


def default_policy() -> QualityGatePolicy:
    return QualityGatePolicy(
        name="default",
        rules=[
            QualityGateRule(metric="accuracy_pct", operator=">=", value=90),
            QualityGateRule(metric="tool_selection_pct", operator=">=", value=95),
            QualityGateRule(metric="regression_delta", operator=">=", value=-3),
        ],
    )


def test_all_metrics_within_policy_passes():
    result = evaluate_quality_gate(
        "exp-1",
        make_summary(91.7),
        tool_selection_pct=100.0,
        regression_delta=0.0,
        policy=default_policy(),
    )
    assert result.passed is True
    assert all(r.passed for r in result.rule_results)


def test_one_metric_below_threshold_fails_with_specific_rule_identified():
    result = evaluate_quality_gate(
        "exp-1",
        make_summary(80.0),  # below 90
        tool_selection_pct=100.0,
        regression_delta=0.0,
        policy=default_policy(),
    )
    assert result.passed is False
    accuracy_rule = next(r for r in result.rule_results if r.metric == "accuracy_pct")
    assert accuracy_rule.passed is False
    assert accuracy_rule.actual == 80.0
    other_rules = [r for r in result.rule_results if r.metric != "accuracy_pct"]
    assert all(r.passed for r in other_rules)


def test_regression_delta_rule_skipped_without_baseline_does_not_block_others():
    result = evaluate_quality_gate(
        "exp-1",
        make_summary(91.7),
        tool_selection_pct=100.0,
        regression_delta=None,  # no --baseline provided
        policy=default_policy(),
    )
    regression_rule = next(r for r in result.rule_results if r.metric == "regression_delta")
    assert regression_rule.passed is None
    assert result.passed is True  # other rules still pass


def test_all_rules_skipped_means_overall_fail_not_silent_pass():
    policy = QualityGatePolicy(
        name="only-regression",
        rules=[QualityGateRule(metric="regression_delta", operator=">=", value=-3)],
    )
    result = evaluate_quality_gate(
        "exp-1", make_summary(91.7), tool_selection_pct=None, regression_delta=None, policy=policy
    )
    assert result.rule_results[0].passed is None
    assert result.passed is False


def test_operator_lte_and_eq_work():
    policy = QualityGatePolicy(
        name="custom",
        rules=[
            QualityGateRule(metric="accuracy_pct", operator="<=", value=100),
            QualityGateRule(metric="accuracy_pct", operator="==", value=91.7),
        ],
    )
    result = evaluate_quality_gate(
        "exp-1", make_summary(91.7), tool_selection_pct=None, regression_delta=None, policy=policy
    )
    assert result.passed is True

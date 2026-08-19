from typing import Literal

from pydantic import BaseModel


class QualityGateRule(BaseModel):
    model_config = {"extra": "forbid"}

    metric: str
    operator: Literal[">=", "<=", "=="]
    value: float


class QualityGatePolicy(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    rules: list[QualityGateRule]


class QualityGateRuleResult(BaseModel):
    model_config = {"extra": "forbid"}

    metric: str
    operator: str
    expected: float
    actual: float | None = None
    passed: bool | None = None


class QualityGateResult(BaseModel):
    model_config = {"extra": "forbid"}

    experiment_id: str
    policy_name: str
    passed: bool
    rule_results: list[QualityGateRuleResult]

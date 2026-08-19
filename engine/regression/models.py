from pydantic import BaseModel


class RegressionResult(BaseModel):
    model_config = {"extra": "forbid"}

    baseline_experiment_id: str
    candidate_experiment_id: str
    baseline_accuracy_pct: float
    candidate_accuracy_pct: float
    accuracy_delta: float
    regressed: bool
    threshold_pct: float
    regressed_cases: list[str]

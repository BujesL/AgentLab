from pydantic import BaseModel


class EvalScore(BaseModel):
    model_config = {"extra": "forbid"}

    metric: str
    score: float
    passed: bool
    reason: str | None = None


class EvaluationResult(BaseModel):
    model_config = {"extra": "forbid"}

    case_id: str
    scores: dict[str, float]
    passed: bool
    failure_reason: str | None = None

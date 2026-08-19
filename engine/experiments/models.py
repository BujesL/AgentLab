from typing import Literal

from pydantic import BaseModel


class Agent(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    name: str
    description: str = ""


class AgentVersion(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    agent_id: str
    version: str
    code_ref: str = ""


class Experiment(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    agent_version_id: str
    dataset_id: str
    model: str
    config: dict = {}
    status: Literal["running", "completed", "failed"] = "running"
    prompt_version_id: str | None = None


class ExperimentSummary(BaseModel):
    model_config = {"extra": "forbid"}

    experiment_id: str
    total_cases: int
    passed: int
    accuracy_pct: float
    avg_latency_ms: float
    avg_cost: float

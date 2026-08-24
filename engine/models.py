from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class EvaluationCase(BaseModel):
    model_config = {"extra": "forbid"}

    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    input: str = Field(min_length=1)
    expected_tools: list[str] = Field(default_factory=list)
    expected_arguments: dict | None = None
    expected_answer: dict | None = None
    expected_behavior: Literal["answer", "refuse", "clarify"] = "answer"
    requires_approval: bool = False
    context: list[str] | None = None
    expected_agent: str | None = None

    @model_validator(mode="after")
    def refuse_has_no_expected_answer(self) -> "EvaluationCase":
        if self.expected_behavior == "refuse" and self.expected_answer is not None:
            raise ValueError(
                f"case {self.id}: expected_behavior='refuse' cannot have expected_answer set"
            )
        return self


class Dataset(BaseModel):
    model_config = {"extra": "forbid"}

    id: str = Field(pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    description: str = ""
    cases: list[EvaluationCase] = Field(min_length=1)

    @field_validator("cases")
    @classmethod
    def unique_case_ids(cls, cases: list[EvaluationCase]) -> list[EvaluationCase]:
        seen: set[str] = set()
        for case in cases:
            if case.id in seen:
                raise ValueError(f"duplicate evaluation case id: {case.id}")
            seen.add(case.id)
        return cases

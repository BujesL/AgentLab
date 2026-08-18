from typing import Literal

from pydantic import BaseModel, Field


class ToolSpec(BaseModel):
    model_config = {"extra": "forbid"}

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    input_schema: dict
    output_schema: dict | None = None
    risk_level: Literal["low", "medium", "high"] = "low"
    requires_approval: bool = False
    enabled_for_evaluation: bool = True


class ToolCall(BaseModel):
    model_config = {"extra": "forbid"}

    tool_name: str
    arguments: dict
    result: dict | None = None

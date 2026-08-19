from pydantic import BaseModel


class PromptVersion(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    name: str
    version: str
    content_hash: str

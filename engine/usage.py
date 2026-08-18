from pydantic import BaseModel


class TokenUsage(BaseModel):
    model_config = {"extra": "forbid"}

    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

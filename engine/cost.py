from engine.usage import TokenUsage

# Placeholder pricing table — NOT official/current provider rate cards.
# Update these values from the provider's real pricing page before using
# estimate_cost() for any real cost decision (see docs/specs/token-cost-tracking/spec.md).
PRICING: dict[str, dict[str, float]] = {
    "mock": {"prompt_per_1k": 0.0, "completion_per_1k": 0.0},
    "claude-placeholder": {"prompt_per_1k": 0.003, "completion_per_1k": 0.015},
}


def estimate_cost(usage: TokenUsage | None, model: str = "mock") -> float:
    if usage is None:
        return 0.0
    pricing = PRICING.get(model, PRICING["mock"])
    return (usage.prompt_tokens / 1000) * pricing["prompt_per_1k"] + (
        usage.completion_tokens / 1000
    ) * pricing["completion_per_1k"]

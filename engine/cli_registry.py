from engine.tools.models import ToolSpec
from engine.tools.registry import ToolRegistry


def build_default_registry() -> ToolRegistry:
    """Tool registry matching datasets/service-desk-mvp/dataset.json.

    A dataset-specific tool registry mechanism (so a new dataset doesn't need
    a hand-maintained Python function) is a V1 improvement — out of scope
    here (see docs/specs/cli/plan.md).
    """
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="get_tickets",
            description="List tickets matching filters",
            input_schema={"type": "object"},
        ),
        stub_result={"count": 4},
    )
    registry.register(
        ToolSpec(
            name="update_ticket",
            description="Update a ticket's fields",
            input_schema={"type": "object"},
            risk_level="medium",
            requires_approval=True,
        ),
    )
    registry.register(
        ToolSpec(
            name="delete_all_tickets",
            description="Delete all tickets (destructive)",
            input_schema={"type": "object"},
            risk_level="high",
            requires_approval=True,
        ),
    )
    registry.register(
        ToolSpec(
            name="cancel_subscription",
            description="Cancel the company subscription (destructive)",
            input_schema={"type": "object"},
            risk_level="high",
            requires_approval=True,
        ),
    )
    return registry

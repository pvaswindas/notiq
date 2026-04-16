from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class Channel:
    """Legacy channel entity for compatibility event fan-out routing.

    Purpose:
    - Describe a destination/provider configuration for compatibility and admin flows.

    Responsibilities:
    - Provide workspace-scoped provider routing inputs.
    - Carry optional provider configuration payload.

    Architectural role:
    - Compatibility model used outside the primary modular notifications domain.

    Constraints:
    - `id`, `workspace_id`, and `provider` must be present.
    """

    id: str
    workspace_id: str
    provider: str
    group: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate mandatory routing identifiers for enqueue flow.

        Raises:
            ValueError: If id, workspace_id, or provider is empty.
        """

        if not self.id:
            raise ValueError("id is required")
        if not self.workspace_id:
            raise ValueError("workspace_id is required")
        if not self.provider:
            raise ValueError("provider is required")

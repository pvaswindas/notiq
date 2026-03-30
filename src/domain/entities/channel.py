from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class Channel:
    id: str
    workspace_id: str
    provider: str
    config: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id is required")
        if not self.workspace_id:
            raise ValueError("workspace_id is required")
        if not self.provider:
            raise ValueError("provider is required")

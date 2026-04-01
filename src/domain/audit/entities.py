from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True, frozen=True)
class AuditLog:
    id: str
    actor_id: str | None
    action: str
    resource: str
    resource_id: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    metadata: dict[str, Any] | None
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id is required")
        if not self.action:
            raise ValueError("action is required")
        if not self.resource:
            raise ValueError("resource is required")
        if not self.resource_id:
            raise ValueError("resource_id is required")

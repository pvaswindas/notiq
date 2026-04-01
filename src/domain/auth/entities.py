from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class ApiKey:
    id: str
    workspace_id: str
    key_hash: str
    name: str
    is_active: bool
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id is required")
        if not self.workspace_id:
            raise ValueError("workspace_id is required")
        if not self.key_hash:
            raise ValueError("key_hash is required")
        if not self.name:
            raise ValueError("name is required")

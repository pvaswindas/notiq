from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class Workspace:
    id: str
    name: str
    created_at: datetime
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id is required")
        if not self.name:
            raise ValueError("name is required")

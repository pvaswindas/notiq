from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True, frozen=True)
class Workspace:
    """
    Purpose:
    - Represent a tenant boundary in the notifications domain.

    Responsibilities:
    - Store immutable workspace identity and lifecycle state.

    Inputs:
    - workspace_id: str
    - name: str
    - is_active: bool
    - created_at: datetime

    Outputs:
    - Workspace entity instance.

    Constraints:
    - Must remain framework-independent and persistence-agnostic.

    Attributes:
    - workspace_id: Stable tenant identifier.
    - name: Human-readable workspace name.
    - is_active: Availability flag for routing eligibility.
    - created_at: UTC timestamp of creation.
    """

    workspace_id: str
    name: str
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True, frozen=True)
class ProviderAccount:
    """Provider credential binding used to authorize outbound delivery calls.

    A provider account may be scoped to a workspace or defined globally
    (`workspace_id=None`) as a system default fallback.
    """

    provider_account_id: str
    provider_key: str
    credentials: dict[str, Any]
    workspace_id: str | None = None
    is_default: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

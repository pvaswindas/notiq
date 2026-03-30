from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True, frozen=True)
class Channel:
    """Route configuration that maps a workspace event to a provider destination.

    Responsibilities:
    - Identify the provider and destination for a notification path.
    - Optionally pin delivery to a specific provider account.
    - Carry channel metadata used by mapping/policy decisions.
    """

    channel_id: str
    workspace_id: str
    provider_key: str
    destination: str
    provider_account_id: str | None = None
    is_active: bool = True
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True, frozen=True)
class Channel:
    """
    Purpose:
    - Represent a delivery destination configured for a workspace.

    Responsibilities:
    - Hold provider-independent channel metadata used for routing.

    Inputs:
    - channel_id: str
    - workspace_id: str
    - name: str
    - provider_key: str
    - address: str
    - is_active: bool
    - metadata: dict[str, str]
    - created_at: datetime

    Outputs:
    - Channel entity instance.

    Constraints:
    - Must not include provider SDK behavior or infrastructure concerns.

    Attributes:
    - channel_id: Unique channel identifier.
    - workspace_id: Owning workspace identifier.
    - name: Human-readable channel name.
    - provider_key: Provider lookup key, for example `telegram`.
    - address: Provider destination address, for example chat id.
    - is_active: Delivery eligibility flag.
    - metadata: Provider-agnostic additional configuration.
    - created_at: UTC timestamp when channel was registered.
    """

    channel_id: str
    workspace_id: str
    name: str
    provider_key: str
    address: str
    is_active: bool = True
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.channel import Channel


class ChannelRepository(ABC):
    """
    Purpose:
    - Define repository contract for channel retrieval.

    Responsibilities:
    - Provide active channels for a workspace without exposing persistence details.

    Inputs:
    - workspace_id: str

    Outputs:
    - list[Channel]

    Constraints:
    - Implementations must be asynchronous and non-blocking.
    """

    @abstractmethod
    async def list_active_by_workspace(self, workspace_id: str) -> list[Channel]:
        """
        Purpose:
        - Fetch active channels for a workspace.

        Responsibilities:
        - Return only active channels eligible for delivery.

        Inputs:
        - workspace_id: str

        Outputs:
        - list[Channel]

        Constraints:
        - Must not raise for unknown workspaces.
        """


class IdempotencyRepository(ABC):
    """
    Purpose:
    - Define storage contract for deduplication keys.

    Responsibilities:
    - Check and atomically claim processed fingerprints.

    Inputs:
    - dedupe_key: str

    Outputs:
    - bool or None depending on operation.

    Constraints:
    - Implementations must be asynchronous.
    """

    @abstractmethod
    async def exists(self, dedupe_key: str) -> bool:
        """
        Purpose:
        - Check if dedupe key has already been recorded.

        Responsibilities:
        - Return idempotency state for routing decisions.

        Inputs:
        - dedupe_key: str

        Outputs:
        - bool

        Constraints:
        - Must return False for unknown keys.
        """

    @abstractmethod
    async def claim(self, dedupe_key: str) -> bool:
        """
        Purpose:
        - Atomically claim a dedupe key for first-time processing.

        Responsibilities:
        - Persist key if absent and return True.
        - Return False when key already exists.

        Inputs:
        - dedupe_key: str

        Outputs:
        - bool

        Constraints:
        - Must be concurrency-safe.
        """

    @abstractmethod
    async def save(self, dedupe_key: str) -> None:
        """
        Purpose:
        - Persist a dedupe key.

        Responsibilities:
        - Record key for future duplicate suppression.

        Inputs:
        - dedupe_key: str

        Outputs:
        - None

        Constraints:
        - Must be idempotent across repeated saves.
        """

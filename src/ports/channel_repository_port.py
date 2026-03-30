from abc import ABC, abstractmethod

from src.domain.entities.channel import Channel


class ChannelRepositoryPort(ABC):
    """Contract for retrieving active channels in legacy ingestion flow."""

    @abstractmethod
    async def get_active_channels(self, workspace_id: str) -> list[Channel]:
        """Return active channels for a workspace.

        Args:
            workspace_id: Tenant identifier used for channel filtering.

        Returns:
            list[Channel]: Active channel entities for the workspace.
        """

        ...

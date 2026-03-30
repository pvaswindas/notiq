from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.channel import Channel


class ChannelRepositoryPort(ABC):
    """Port for reading channel routing configuration from persistence."""

    @abstractmethod
    async def list_active_by_workspace(self, workspace_id: str) -> list[Channel]:
        """Return active channels for a workspace."""

        pass

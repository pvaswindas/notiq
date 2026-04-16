from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.channel import Channel


class ChannelRepositoryPort(ABC):
    """Port for reading channel routing configuration from persistence."""

    @abstractmethod
    async def create(self, channel: Channel) -> Channel:
        """Persist a channel definition."""

        pass

    @abstractmethod
    async def get_by_id(self, channel_id: str, workspace_id: str) -> Channel | None:
        """Fetch one channel by id within a workspace."""

        pass

    @abstractmethod
    async def list_by_workspace(self, workspace_id: str) -> list[Channel]:
        """Return all channels for a workspace."""

        pass

    @abstractmethod
    async def list_active_by_workspace(self, workspace_id: str) -> list[Channel]:
        """Return active channels for a workspace."""

        pass

    @abstractmethod
    async def update(self, channel: Channel) -> Channel:
        """Persist channel changes."""

        pass

    @abstractmethod
    async def find_by_route(
        self,
        workspace_id: str,
        provider_key: str,
        provider_account_id: str,
        destination: str,
    ) -> Channel | None:
        """Find a channel with the same workspace/provider/account/destination tuple."""

        pass

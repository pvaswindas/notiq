from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.channel import Channel


class ChannelRepositoryPort(ABC):
    @abstractmethod
    async def list_active_by_workspace(self, workspace_id: str) -> list[Channel]:
        pass

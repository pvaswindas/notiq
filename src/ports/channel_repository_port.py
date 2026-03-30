from abc import ABC, abstractmethod

from src.domain.entities.channel import Channel


class ChannelRepositoryPort(ABC):
    @abstractmethod
    async def get_active_channels(self, workspace_id: str) -> list[Channel]:
        ...

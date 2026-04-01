from abc import ABC, abstractmethod

from src.domain.entities.channel import Channel


class ChannelRepository(ABC):
    @abstractmethod
    async def get_by_id(self, channel_id: str, workspace_id: str) -> Channel | None:
        ...

    @abstractmethod
    async def list_by_workspace(self, workspace_id: str) -> list[Channel]:
        ...

    @abstractmethod
    async def save(self, channel: Channel) -> Channel:
        ...

    @abstractmethod
    async def update(self, channel: Channel) -> Channel:
        ...

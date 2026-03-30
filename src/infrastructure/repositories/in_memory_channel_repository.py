from collections import defaultdict

from src.domain.entities.channel import Channel
from src.ports.channel_repository_port import ChannelRepositoryPort


class InMemoryChannelRepository(ChannelRepositoryPort):
    def __init__(self, channels: list[Channel] | None = None) -> None:
        self._channels_by_workspace: dict[str, list[Channel]] = defaultdict(list)
        for channel in channels or []:
            self._channels_by_workspace[channel.workspace_id].append(channel)

    async def get_active_channels(self, workspace_id: str) -> list[Channel]:
        channels = self._channels_by_workspace.get(workspace_id, [])
        return [channel for channel in channels if channel.is_active]

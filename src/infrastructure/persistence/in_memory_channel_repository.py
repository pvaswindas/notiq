from collections import defaultdict

from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.repositories import ChannelRepository


class InMemoryChannelRepository(ChannelRepository):
    """
    Purpose:
    - Provide async in-memory channel storage adapter.

    Responsibilities:
    - Store channels by workspace.
    - Return active channels for routing.

    Inputs:
    - list[Channel] during construction.

    Outputs:
    - Repository operations over in-memory structures.

    Constraints:
    - Intended for local development and testing.
    """

    def __init__(self, channels: list[Channel] | None = None) -> None:
        """
        Purpose:
        - Initialize in-memory workspace channel index.

        Responsibilities:
        - Group channels by workspace for retrieval.

        Inputs:
        - channels: Optional list[Channel]

        Outputs:
        - None

        Constraints:
        - Data is process-local and non-persistent.
        """

        self._channels_by_workspace: dict[str, list[Channel]] = defaultdict(list)
        for channel in channels or []:
            self._channels_by_workspace[channel.workspace_id].append(channel)

    async def list_active_by_workspace(self, workspace_id: str) -> list[Channel]:
        """
        Purpose:
        - Return active channels for workspace routing.

        Responsibilities:
        - Filter workspace channel list by active flag.

        Inputs:
        - workspace_id: str

        Outputs:
        - list[Channel]

        Constraints:
        - Must return empty list when workspace has no channels.
        """

        channels = self._channels_by_workspace.get(workspace_id, [])
        return [channel for channel in channels if channel.is_active]

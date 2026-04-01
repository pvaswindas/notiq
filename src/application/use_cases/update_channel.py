from dataclasses import dataclass
from typing import Any

from src.application.services.audit_logger import AuditLogger
from src.domain.entities.channel import Channel
from src.ports.channel_repository import ChannelRepository


@dataclass(slots=True, frozen=True)
class UpdateChannelInput:
    channel_id: str
    workspace_id: str
    provider: str
    config: dict[str, Any] | None = None
    group: str | None = None
    is_active: bool | None = None
    actor_id: str | None = None
    audit_metadata: dict[str, object] | None = None


class UpdateChannelUseCase:
    def __init__(
        self,
        channel_repository: ChannelRepository,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._channel_repository = channel_repository
        self._audit_logger = audit_logger

    async def execute(self, dto: UpdateChannelInput) -> Channel:
        channel_id = dto.channel_id.strip()
        workspace_id = dto.workspace_id.strip()
        provider = dto.provider.strip()

        if not channel_id:
            raise ValueError("channel_id is required")
        if not workspace_id:
            raise ValueError("workspace_id is required")
        if not provider:
            raise ValueError("provider is required")

        current_channel = await self._channel_repository.get_by_id(channel_id, workspace_id)
        if current_channel is None:
            raise LookupError("channel not found")

        updated_channel = Channel(
            id=current_channel.id,
            workspace_id=current_channel.workspace_id,
            provider=provider,
            group=dto.group,
            config=dto.config or {},
            is_active=current_channel.is_active if dto.is_active is None else dto.is_active,
        )

        saved_channel = await self._channel_repository.update(updated_channel)

        if self._audit_logger is not None:
            await self._audit_logger.log(
                actor_id=dto.actor_id,
                action="channel.update",
                resource="channel",
                resource_id=saved_channel.id,
                before={
                    "id": current_channel.id,
                    "workspace_id": current_channel.workspace_id,
                    "provider": current_channel.provider,
                    "group": current_channel.group,
                    "config": current_channel.config,
                    "is_active": current_channel.is_active,
                },
                after={
                    "id": saved_channel.id,
                    "workspace_id": saved_channel.workspace_id,
                    "provider": saved_channel.provider,
                    "group": saved_channel.group,
                    "config": saved_channel.config,
                    "is_active": saved_channel.is_active,
                },
                metadata=dto.audit_metadata,
            )

        return saved_channel

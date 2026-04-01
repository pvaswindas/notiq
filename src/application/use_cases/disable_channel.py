from dataclasses import dataclass

from src.application.services.audit_logger import AuditLogger
from src.domain.entities.channel import Channel
from src.ports.channel_repository import ChannelRepository


@dataclass(slots=True, frozen=True)
class DisableChannelInput:
    channel_id: str
    workspace_id: str
    actor_id: str | None = None
    audit_metadata: dict[str, object] | None = None


class DisableChannelUseCase:
    def __init__(
        self,
        channel_repository: ChannelRepository,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._channel_repository = channel_repository
        self._audit_logger = audit_logger

    async def execute(self, dto: DisableChannelInput) -> Channel:
        channel_id = dto.channel_id.strip()
        workspace_id = dto.workspace_id.strip()

        if not channel_id:
            raise ValueError("channel_id is required")
        if not workspace_id:
            raise ValueError("workspace_id is required")

        current_channel = await self._channel_repository.get_by_id(channel_id, workspace_id)
        if current_channel is None:
            raise LookupError("channel not found")

        if not current_channel.is_active:
            return current_channel

        disabled_channel = Channel(
            id=current_channel.id,
            workspace_id=current_channel.workspace_id,
            provider=current_channel.provider,
            group=current_channel.group,
            config=current_channel.config,
            is_active=False,
        )
        saved_channel = await self._channel_repository.update(disabled_channel)

        if self._audit_logger is not None:
            await self._audit_logger.log(
                actor_id=dto.actor_id,
                action="channel.disable",
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

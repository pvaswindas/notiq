from dataclasses import dataclass

from src.application.services.audit_logger import AuditLogger
from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.ports.channel_repository_port import ChannelRepositoryPort


@dataclass(slots=True, frozen=True)
class DisableManagedChannelCommand:
    channel_id: str
    workspace_id: str
    actor_id: str | None = None
    audit_metadata: dict[str, object] | None = None


class DisableManagedChannelUseCase:
    """Disable one workspace channel."""

    def __init__(
        self,
        channel_repository: ChannelRepositoryPort,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._channel_repository = channel_repository
        self._audit_logger = audit_logger

    async def execute(self, command: DisableManagedChannelCommand) -> Channel:
        channel_id = command.channel_id.strip()
        workspace_id = command.workspace_id.strip()

        if not channel_id:
            raise ValueError("channel_id is required")
        if not workspace_id:
            raise ValueError("workspace_id is required")

        current = await self._channel_repository.get_by_id(channel_id, workspace_id)
        if current is None:
            raise LookupError("channel not found")

        if not current.is_active:
            return current

        disabled = Channel(
            channel_id=current.channel_id,
            workspace_id=current.workspace_id,
            provider_key=current.provider_key,
            destination=current.destination,
            provider_account_id=current.provider_account_id,
            is_active=False,
            metadata=dict(current.metadata),
            created_at=current.created_at,
        )
        saved = await self._channel_repository.update(disabled)

        if self._audit_logger is not None:
            await self._audit_logger.log(
                actor_id=command.actor_id,
                action="channel.disable",
                resource="channel",
                resource_id=saved.channel_id,
                before={
                    "channel_id": current.channel_id,
                    "workspace_id": current.workspace_id,
                    "provider_key": current.provider_key,
                    "provider_account_id": current.provider_account_id,
                    "destination": current.destination,
                    "metadata": current.metadata,
                    "is_active": current.is_active,
                },
                after={
                    "channel_id": saved.channel_id,
                    "workspace_id": saved.workspace_id,
                    "provider_key": saved.provider_key,
                    "provider_account_id": saved.provider_account_id,
                    "destination": saved.destination,
                    "metadata": saved.metadata,
                    "is_active": saved.is_active,
                },
                metadata=command.audit_metadata,
            )

        return saved

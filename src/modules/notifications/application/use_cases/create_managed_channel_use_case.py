from dataclasses import dataclass
from datetime import datetime, timezone

from src.application.services.audit_logger import AuditLogger
from src.modules.notifications.application.errors import ConflictError
from src.modules.notifications.application.services.provider_configuration_validator import (
    ProviderConfigurationValidator,
)
from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.ports.channel_repository_port import ChannelRepositoryPort
from src.modules.notifications.ports.id_generator_port import IdGeneratorPort
from src.modules.notifications.ports.provider_account_repository_port import ProviderAccountRepositoryPort
from src.modules.notifications.ports.workspace_repository_port import WorkspaceRepositoryPort


@dataclass(slots=True, frozen=True)
class CreateManagedChannelCommand:
    workspace_id: str
    provider: str
    provider_account_id: str
    destination: str
    metadata: dict[str, str] | None = None
    actor_id: str | None = None
    audit_metadata: dict[str, object] | None = None


class CreateManagedChannelUseCase:
    """Create a channel linked to an owned provider account."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepositoryPort,
        channel_repository: ChannelRepositoryPort,
        provider_account_repository: ProviderAccountRepositoryPort,
        validator: ProviderConfigurationValidator,
        id_generator: IdGeneratorPort,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._channel_repository = channel_repository
        self._provider_account_repository = provider_account_repository
        self._validator = validator
        self._id_generator = id_generator
        self._audit_logger = audit_logger

    async def execute(self, command: CreateManagedChannelCommand) -> Channel:
        workspace_id = command.workspace_id.strip()
        provider_account_id = command.provider_account_id.strip()

        if not workspace_id:
            raise ValueError("workspace_id is required")
        if not provider_account_id:
            raise ValueError("provider_account_id is required")

        workspace = await self._workspace_repository.get_by_id(workspace_id)
        if workspace is None:
            raise LookupError("workspace not found")

        provider_key = self._validator.normalize_provider(command.provider)
        destination = self._validator.validate_destination(provider_key, command.destination)

        provider_account = await self._provider_account_repository.get_by_id(provider_account_id)
        if provider_account is None or not provider_account.is_active:
            raise LookupError("provider account not found")
        if provider_account.workspace_id != workspace_id:
            raise PermissionError("workspace access denied")
        if provider_account.provider_key != provider_key:
            raise ValueError("provider_account_id does not match provider")

        duplicate = await self._channel_repository.find_by_route(
            workspace_id=workspace_id,
            provider_key=provider_key,
            provider_account_id=provider_account_id,
            destination=destination,
        )
        if duplicate is not None:
            raise ConflictError("channel already exists for this provider account and destination")

        channel = Channel(
            channel_id=f"ch_{self._id_generator.new_id()}",
            workspace_id=workspace_id,
            provider_key=provider_key,
            destination=destination,
            provider_account_id=provider_account_id,
            is_active=True,
            metadata=dict(command.metadata or {}),
            created_at=datetime.now(timezone.utc),
        )
        created = await self._channel_repository.create(channel)

        if self._audit_logger is not None:
            await self._audit_logger.log(
                actor_id=command.actor_id,
                action="channel.create",
                resource="channel",
                resource_id=created.channel_id,
                before=None,
                after={
                    "channel_id": created.channel_id,
                    "workspace_id": created.workspace_id,
                    "provider_key": created.provider_key,
                    "provider_account_id": created.provider_account_id,
                    "destination": created.destination,
                    "metadata": created.metadata,
                    "is_active": created.is_active,
                },
                metadata=command.audit_metadata,
            )

        return created

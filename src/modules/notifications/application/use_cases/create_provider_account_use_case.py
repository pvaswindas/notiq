from dataclasses import dataclass
from datetime import datetime, timezone

from src.application.services.audit_logger import AuditLogger
from src.modules.notifications.application.services.provider_configuration_validator import (
    ProviderConfigurationValidator,
)
from src.modules.notifications.domain.entities.provider_account import ProviderAccount
from src.modules.notifications.ports.id_generator_port import IdGeneratorPort
from src.modules.notifications.ports.provider_account_repository_port import ProviderAccountRepositoryPort
from src.modules.notifications.ports.workspace_repository_port import WorkspaceRepositoryPort


@dataclass(slots=True, frozen=True)
class CreateProviderAccountCommand:
    workspace_id: str
    provider: str
    credentials: dict
    actor_id: str | None = None
    audit_metadata: dict[str, object] | None = None


class CreateProviderAccountUseCase:
    """Create a workspace-scoped provider account without exposing credentials."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepositoryPort,
        provider_account_repository: ProviderAccountRepositoryPort,
        validator: ProviderConfigurationValidator,
        id_generator: IdGeneratorPort,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._workspace_repository = workspace_repository
        self._provider_account_repository = provider_account_repository
        self._validator = validator
        self._id_generator = id_generator
        self._audit_logger = audit_logger

    async def execute(self, command: CreateProviderAccountCommand) -> ProviderAccount:
        workspace_id = command.workspace_id.strip()
        if not workspace_id:
            raise ValueError("workspace_id is required")

        workspace = await self._workspace_repository.get_by_id(workspace_id)
        if workspace is None:
            raise LookupError("workspace not found")

        provider_key = self._validator.normalize_provider(command.provider)
        credentials = self._validator.validate_credentials(provider_key, command.credentials)

        provider_account = ProviderAccount(
            provider_account_id=f"pa_{self._id_generator.new_id()}",
            workspace_id=workspace_id,
            provider_key=provider_key,
            credentials=credentials,
            is_default=False,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        created = await self._provider_account_repository.create(provider_account)

        if self._audit_logger is not None:
            await self._audit_logger.log(
                actor_id=command.actor_id,
                action="provider_account.create",
                resource="provider_account",
                resource_id=created.provider_account_id,
                before=None,
                after={
                    "provider_account_id": created.provider_account_id,
                    "workspace_id": created.workspace_id,
                    "provider_key": created.provider_key,
                    "credentials": created.credentials,
                    "is_active": created.is_active,
                },
                metadata=command.audit_metadata,
            )

        return created

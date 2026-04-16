from dataclasses import dataclass

from src.modules.notifications.domain.entities.provider_account import ProviderAccount
from src.modules.notifications.ports.provider_account_repository_port import ProviderAccountRepositoryPort


@dataclass(slots=True, frozen=True)
class GetProviderAccountCommand:
    provider_account_id: str
    workspace_id: str


class GetProviderAccountUseCase:
    """Load one provider account while enforcing workspace ownership."""

    def __init__(self, provider_account_repository: ProviderAccountRepositoryPort) -> None:
        self._provider_account_repository = provider_account_repository

    async def execute(self, command: GetProviderAccountCommand) -> ProviderAccount:
        provider_account_id = command.provider_account_id.strip()
        workspace_id = command.workspace_id.strip()

        if not provider_account_id:
            raise ValueError("provider_account_id is required")
        if not workspace_id:
            raise ValueError("workspace_id is required")

        provider_account = await self._provider_account_repository.get_by_id(provider_account_id)
        if provider_account is None:
            raise LookupError("provider account not found")
        if provider_account.workspace_id != workspace_id:
            raise PermissionError("workspace access denied")

        return provider_account

from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.entities.provider_account import ProviderAccount
from src.modules.notifications.ports.provider_account_repository_port import ProviderAccountRepositoryPort


class ProviderAccountResolver:
    """Resolve the effective provider account for a channel delivery attempt."""

    def __init__(self, provider_account_repository: ProviderAccountRepositoryPort) -> None:
        """Store provider account repository dependency used for lookup/fallback."""

        self._provider_account_repository = provider_account_repository

    async def resolve_for_channel(self, channel: Channel) -> ProviderAccount:
        """Resolve account in this order: channel-specific, workspace default, system default.

        Raises:
        - ValueError: If no active account can be resolved for the channel.
        """

        if channel.provider_account_id:
            account = await self._provider_account_repository.get_by_id(channel.provider_account_id)
            if account is None or not account.is_active:
                raise ValueError(f"inactive or missing provider account: {channel.provider_account_id}")
            return account

        workspace_default = await self._provider_account_repository.get_default(
            provider_key=channel.provider_key,
            workspace_id=channel.workspace_id,
        )
        if workspace_default is not None and workspace_default.is_active:
            return workspace_default

        system_default = await self._provider_account_repository.get_default(
            provider_key=channel.provider_key,
            workspace_id=None,
        )
        if system_default is None or not system_default.is_active:
            raise ValueError(f"missing default provider account for provider={channel.provider_key}")
        return system_default

from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.entities.provider_account import ProviderAccount
from src.modules.notifications.ports.provider_account_repository_port import ProviderAccountRepositoryPort


class ProviderAccountResolver:
    """Resolve the effective provider account for a channel delivery attempt."""

    def __init__(self, provider_account_repository: ProviderAccountRepositoryPort) -> None:
        """Store provider account repository dependency used for lookup/fallback."""

        self._provider_account_repository = provider_account_repository

    async def resolve_for_channel(self, channel: Channel) -> ProviderAccount:
        """Resolve the explicit provider account configured for a channel.

        Raises:
        - ValueError: If the channel is missing an account or the account is invalid.
        """

        if not channel.provider_account_id:
            raise ValueError(f"channel {channel.channel_id} is missing provider_account_id")

        account = await self._provider_account_repository.get_by_id(channel.provider_account_id)
        if account is None or not account.is_active:
            raise ValueError(f"inactive or missing provider account: {channel.provider_account_id}")
        if account.provider_key != channel.provider_key:
            raise ValueError(
                f"provider account {channel.provider_account_id} does not match channel provider {channel.provider_key}"
            )
        if account.workspace_id != channel.workspace_id:
            raise ValueError(
                f"provider account {channel.provider_account_id} does not belong to workspace {channel.workspace_id}"
            )

        return account

import logging

import httpx

from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.entities.provider_account import ProviderAccount
from src.modules.notifications.ports.notification_sender_port import NotificationSenderPort


class TelegramNotifier(NotificationSenderPort):
    """Outbound adapter that sends delivery jobs through Telegram APIs."""

    def __init__(self) -> None:
        """Initialize adapter logger used for delivery telemetry."""

        self._logger = logging.getLogger(__name__)

    async def send(self, channel: Channel, provider_account: ProviderAccount, event: dict) -> None:
        """Send a notification through the Telegram Bot API."""

        if provider_account.provider_key != "telegram":
            raise ValueError("telegram sender received non-telegram provider account")
        if not isinstance(provider_account.credentials, dict):
            raise ValueError("telegram provider account credentials must be a JSON object")

        bot_token = self._require_string(provider_account.credentials, "bot_token")
        destination = channel.destination.strip() or self._optional_string(provider_account.credentials, "default_chat_id")
        if not destination:
            raise ValueError(f"telegram destination missing for channel {channel.channel_id}")

        text = self._build_message(event)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        self._logger.info(
            "telegram notification sending",
            extra={
                "workspace_id": channel.workspace_id,
                "channel_id": channel.channel_id,
                "provider_account_id": provider_account.provider_account_id,
                "destination": destination,
            },
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json={
                        "chat_id": destination,
                        "text": text,
                    },
                )
                response.raise_for_status()
                response_json = response.json()
                if not response_json.get("ok", False):
                    raise ValueError(f"telegram api rejected message: {response_json}")
        except Exception:
            self._logger.exception(
                "telegram notification failed",
                extra={
                    "workspace_id": channel.workspace_id,
                    "channel_id": channel.channel_id,
                    "provider_account_id": provider_account.provider_account_id,
                    "destination": destination,
                },
            )
            raise

        self._logger.info(
            "telegram notification sent",
            extra={
                "workspace_id": channel.workspace_id,
                "channel_id": channel.channel_id,
                "provider_account_id": provider_account.provider_account_id,
                "destination": destination,
            },
        )

    @staticmethod
    def _build_message(event: dict) -> str:
        """Construct the Telegram message body from the notification event payload."""

        message_value = event.get("message")
        if not isinstance(message_value, str) or not message_value.strip():
            raise ValueError("telegram event missing required string field: message")

        title_value = event.get("title")
        title = title_value.strip() if isinstance(title_value, str) else ""
        message = message_value.strip()
        if title:
            return f"{title}\n{message}"
        return message

    @staticmethod
    def _require_string(data: dict, key: str) -> str:
        """Return a required non-empty string value from provider credentials."""

        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"telegram provider credentials missing required field: {key}")
        return value.strip()

    @staticmethod
    def _optional_string(data: dict, key: str) -> str:
        """Return an optional string value from provider credentials."""

        value = data.get(key)
        if not isinstance(value, str):
            return ""
        return value.strip()

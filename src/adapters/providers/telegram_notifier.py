from typing import Any

import httpx

from src.domain.entities.channel import Channel
from src.domain.entities.event import Event
from src.ports.provider import NotificationProviderPort


class TelegramNotifier(NotificationProviderPort):
    def __init__(self, base_url: str = "https://api.telegram.org") -> None:
        self._base_url = base_url.rstrip("/")

    async def send(self, channel: Channel, event: Event) -> None:
        message = self._format_message(event)
        bot_token = self._read_required_config(channel, "bot_token")
        chat_id = self._read_required_config(channel, "chat_id")
        endpoint = f"{self._base_url}/bot{bot_token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": message,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, dict) or data.get("ok") is not True:
            raise RuntimeError("telegram delivery failed")

    def _format_message(self, event: Event) -> str:
        payload_lines = [f"{key}: {value}" for key, value in event.payload.items()]
        payload_text = "\n".join(payload_lines) if payload_lines else "(no payload)"
        return (
            "Notiq Event\n"
            f"Workspace: {event.workspace_id}\n"
            f"Type: {event.event_type}\n"
            f"Payload:\n{payload_text}"
        )

    def _read_required_config(self, channel: Channel, key: str) -> str:
        value: Any = channel.config.get(key)
        if isinstance(value, str) and value.strip():
            return value
        raise ValueError(f"channel config missing required telegram field: {key}")

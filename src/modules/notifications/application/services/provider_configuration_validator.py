import re
from email.utils import parseaddr
from typing import Any


class ProviderConfigurationValidator:
    """Centralize provider support and basic payload validation rules."""

    _SUPPORTED_PROVIDERS = frozenset({"email", "telegram"})
    _TELEGRAM_CHAT_ID_PATTERN = re.compile(r"^-?\d+$")

    def normalize_provider(self, provider: str) -> str:
        normalized = provider.strip().lower()
        if not normalized:
            raise ValueError("provider is required")
        if normalized not in self._SUPPORTED_PROVIDERS:
            raise ValueError(f"unsupported provider: {normalized}")
        return normalized

    def validate_credentials(self, provider: str, credentials: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(credentials, dict):
            raise ValueError("credentials must be an object")

        normalized_provider = self.normalize_provider(provider)
        if normalized_provider == "telegram":
            return self._validate_telegram_credentials(credentials)
        if normalized_provider == "email":
            return self._validate_email_credentials(credentials)
        raise ValueError(f"unsupported provider: {normalized_provider}")

    def validate_destination(self, provider: str, destination: str) -> str:
        normalized_provider = self.normalize_provider(provider)
        normalized_destination = destination.strip()
        if not normalized_destination:
            raise ValueError("destination is required")

        if normalized_provider == "telegram":
            if self._TELEGRAM_CHAT_ID_PATTERN.fullmatch(normalized_destination) is None:
                raise ValueError("telegram destination must be a numeric chat_id")
            return normalized_destination

        if normalized_provider == "email":
            if not self._is_valid_email(normalized_destination):
                raise ValueError("email destination must be a valid email address")
            return normalized_destination.lower()

        raise ValueError(f"unsupported provider: {normalized_provider}")

    def _validate_telegram_credentials(self, credentials: dict[str, Any]) -> dict[str, Any]:
        bot_token = self._require_non_empty_string(credentials, "bot_token")
        normalized: dict[str, Any] = {"bot_token": bot_token}

        default_chat_id = credentials.get("default_chat_id")
        if default_chat_id is not None:
            default_chat_id_value = str(default_chat_id).strip()
            if self._TELEGRAM_CHAT_ID_PATTERN.fullmatch(default_chat_id_value) is None:
                raise ValueError("telegram default_chat_id must be numeric")
            normalized["default_chat_id"] = default_chat_id_value

        return normalized

    def _validate_email_credentials(self, credentials: dict[str, Any]) -> dict[str, Any]:
        normalized = {
            str(key): value
            for key, value in credentials.items()
            if isinstance(key, str)
        }

        non_empty_string_keys = [
            key
            for key, value in normalized.items()
            if isinstance(value, str) and value.strip()
        ]
        if not non_empty_string_keys:
            raise ValueError("email credentials must include at least one non-empty string field")

        from_email = normalized.get("from_email")
        if from_email is not None:
            if not isinstance(from_email, str) or not self._is_valid_email(from_email.strip()):
                raise ValueError("email from_email must be a valid email address")
            normalized["from_email"] = from_email.strip().lower()

        return normalized

    @staticmethod
    def _require_non_empty_string(data: dict[str, Any], key: str) -> str:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"credentials.{key} is required")
        return value.strip()

    @staticmethod
    def _is_valid_email(value: str) -> bool:
        _, parsed = parseaddr(value)
        return bool(parsed and "@" in parsed and "." in parsed.rsplit("@", 1)[-1])

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.domain.audit.entities import AuditLog
from src.ports.audit_log_repository import AuditLogRepository


class AuditLogger:
    _SENSITIVE_KEYS = {
        "password",
        "password_hash",
        "passphrase",
        "secret",
        "api_key",
        "raw_api_key",
        "token",
        "access_token",
        "refresh_token",
        "private_key",
        "client_secret",
        "authorization",
    }

    def __init__(self, audit_log_repository: AuditLogRepository) -> None:
        self._audit_log_repository = audit_log_repository

    async def log(
        self,
        actor_id: str | None,
        action: str,
        resource: str,
        resource_id: str,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        normalized_actor_id = actor_id.strip() if isinstance(actor_id, str) else None
        sanitized_before = self._sanitize(before)
        sanitized_after = self._sanitize(after)
        sanitized_metadata = self._sanitize(metadata)

        audit_log = AuditLog(
            id=f"aud_{uuid4().hex[:24]}",
            actor_id=normalized_actor_id or None,
            action=action.strip(),
            resource=resource.strip(),
            resource_id=resource_id.strip(),
            before=sanitized_before,
            after=sanitized_after,
            metadata=sanitized_metadata,
            created_at=datetime.now(timezone.utc),
        )
        return await self._audit_log_repository.create(audit_log)

    @classmethod
    def _sanitize(cls, value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, dict):
            sanitized: dict[str, Any] = {}
            for key, item in value.items():
                normalized_key = str(key).lower()
                if cls._is_sensitive_key(normalized_key):
                    sanitized[str(key)] = "***"
                else:
                    sanitized[str(key)] = cls._sanitize(item)
            return sanitized

        if isinstance(value, list):
            return [cls._sanitize(item) for item in value]

        if isinstance(value, tuple):
            return [cls._sanitize(item) for item in value]

        return value

    @classmethod
    def _is_sensitive_key(cls, key: str) -> bool:
        if key in cls._SENSITIVE_KEYS:
            return True
        return "password" in key or "secret" in key or "api_key" in key or key.endswith("token")

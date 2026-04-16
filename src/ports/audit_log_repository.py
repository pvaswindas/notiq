from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.domain.audit.entities import AuditLog


class AuditLogRepository(ABC):
    @abstractmethod
    async def create(self, audit_log: AuditLog) -> AuditLog:
        ...

    @abstractmethod
    async def list(self, filters: dict[str, Any]) -> list[AuditLog]:
        ...

    @abstractmethod
    async def get_by_resource(self, resource: str, resource_id: str) -> list[AuditLog]:
        ...

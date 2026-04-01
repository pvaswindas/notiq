from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, select

from src.domain.audit.entities import AuditLog
from src.infrastructure.database.models import AuditLogModel
from src.infrastructure.database.session import AsyncSessionLocal
from src.ports.audit_log_repository import AuditLogRepository


class PostgresAuditLogRepository(AuditLogRepository):
    async def create(self, audit_log: AuditLog) -> AuditLog:
        async with AsyncSessionLocal() as session:
            model = self._to_model(audit_log)
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def list(self, filters: dict[str, Any]) -> list[AuditLog]:
        async with AsyncSessionLocal() as session:
            statements = []

            actor_id = filters.get("actor_id")
            if actor_id:
                statements.append(AuditLogModel.actor_id == str(actor_id))

            resource = filters.get("resource")
            if resource:
                statements.append(AuditLogModel.resource == str(resource))

            resource_id = filters.get("resource_id")
            if resource_id:
                statements.append(AuditLogModel.resource_id == str(resource_id))

            action = filters.get("action")
            if action:
                statements.append(AuditLogModel.action == str(action))

            created_from = filters.get("created_from")
            if isinstance(created_from, datetime):
                statements.append(AuditLogModel.created_at >= created_from)

            created_to = filters.get("created_to")
            if isinstance(created_to, datetime):
                statements.append(AuditLogModel.created_at <= created_to)

            query = select(AuditLogModel).order_by(AuditLogModel.created_at.desc(), AuditLogModel.id.desc())
            if statements:
                query = query.where(and_(*statements))

            limit = int(filters.get("limit", 50))
            offset = int(filters.get("offset", 0))
            query = query.limit(limit).offset(offset)

            result = await session.execute(query)
            return [self._to_domain(model) for model in result.scalars().all()]

    async def get_by_resource(self, resource: str, resource_id: str) -> list[AuditLog]:
        return await self.list(
            {
                "resource": resource,
                "resource_id": resource_id,
                "limit": 100,
                "offset": 0,
            }
        )

    @staticmethod
    def _to_model(audit_log: AuditLog) -> AuditLogModel:
        return AuditLogModel(
            id=audit_log.id,
            actor_id=audit_log.actor_id,
            action=audit_log.action,
            resource=audit_log.resource,
            resource_id=audit_log.resource_id,
            before=audit_log.before,
            after=audit_log.after,
            audit_metadata=audit_log.metadata,
            created_at=audit_log.created_at,
        )

    @staticmethod
    def _to_domain(model: AuditLogModel) -> AuditLog:
        return AuditLog(
            id=model.id,
            actor_id=model.actor_id,
            action=model.action,
            resource=model.resource,
            resource_id=model.resource_id,
            before=model.before,
            after=model.after,
            metadata=model.audit_metadata,
            created_at=model.created_at,
        )

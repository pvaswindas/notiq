from datetime import datetime
from typing import Any, Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from src.adapters.http.dependencies.admin_auth import AdminAuthContext, require_permission
from src.infrastructure.database.repositories.postgres_audit_log_repository import PostgresAuditLogRepository


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    actor_id: str | None
    action: str
    resource: str
    resource_id: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    metadata: dict[str, Any] | None
    created_at: str


class PaginatedAuditLogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int
    page_size: int
    has_more: bool
    items: list[AuditLogResponse]


class AdminAuditControllerFactory:
    def __init__(self) -> None:
        self._audit_log_repository = PostgresAuditLogRepository()

    def build(self) -> APIRouter:
        router = APIRouter(prefix="/admin", tags=["admin-audit"])

        @router.get(
            "/audit-logs",
            response_model=PaginatedAuditLogResponse,
        )
        async def list_audit_logs(
            auth: Annotated[AdminAuthContext, Depends(require_permission("view_audit_logs"))],
            actor_id: str | None = None,
            resource: str | None = None,
            action: str | None = None,
            from_date: datetime | None = Query(default=None),
            to_date: datetime | None = Query(default=None),
            page: int = Query(default=1, ge=1),
            page_size: int = Query(default=50, ge=1, le=200),
        ) -> PaginatedAuditLogResponse:
            _ = auth

            offset = (page - 1) * page_size
            logs = await self._audit_log_repository.list(
                {
                    "actor_id": actor_id,
                    "resource": resource,
                    "action": action,
                    "created_from": from_date,
                    "created_to": to_date,
                    "offset": offset,
                    "limit": page_size + 1,
                }
            )
            has_more = len(logs) > page_size
            page_items = logs[:page_size]

            return PaginatedAuditLogResponse(
                page=page,
                page_size=page_size,
                has_more=has_more,
                items=[
                    AuditLogResponse(
                        id=log.id,
                        actor_id=log.actor_id,
                        action=log.action,
                        resource=log.resource,
                        resource_id=log.resource_id,
                        before=log.before,
                        after=log.after,
                        metadata=log.metadata,
                        created_at=log.created_at.isoformat(),
                    )
                    for log in page_items
                ],
            )

        @router.get(
            "/audit-logs/{resource}/{resource_id}",
            response_model=PaginatedAuditLogResponse,
        )
        async def get_resource_audit_logs(
            resource: str,
            resource_id: str,
            auth: Annotated[AdminAuthContext, Depends(require_permission("view_audit_logs"))],
            page: int = Query(default=1, ge=1),
            page_size: int = Query(default=50, ge=1, le=200),
        ) -> PaginatedAuditLogResponse:
            _ = auth

            offset = (page - 1) * page_size
            logs = await self._audit_log_repository.list(
                {
                    "resource": resource,
                    "resource_id": resource_id,
                    "offset": offset,
                    "limit": page_size + 1,
                }
            )
            has_more = len(logs) > page_size
            page_items = logs[:page_size]

            return PaginatedAuditLogResponse(
                page=page,
                page_size=page_size,
                has_more=has_more,
                items=[
                    AuditLogResponse(
                        id=log.id,
                        actor_id=log.actor_id,
                        action=log.action,
                        resource=log.resource,
                        resource_id=log.resource_id,
                        before=log.before,
                        after=log.after,
                        metadata=log.metadata,
                        created_at=log.created_at.isoformat(),
                    )
                    for log in page_items
                ],
            )

        return router

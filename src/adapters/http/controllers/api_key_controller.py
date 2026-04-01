from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from src.adapters.http.dependencies.auth import AuthContext, require_auth
from src.application.services.audit_logger import AuditLogger
from src.application.services.auth_service import AuthService
from src.infrastructure.database.repositories.postgres_audit_log_repository import PostgresAuditLogRepository
from src.infrastructure.database.repositories.postgres_api_key_repository import PostgresApiKeyRepository
from src.infrastructure.database.repositories.postgres_workspace_repository import PostgresWorkspaceRepository


class CreateApiKeyRequest(BaseModel):
    """Inbound payload for creating a new workspace API key label."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)


class CreateApiKeyResponse(BaseModel):
    """Outbound contract for one-time API key material return."""

    model_config = ConfigDict(extra="forbid")

    api_key: str
    name: str


class ApiKeyResponse(BaseModel):
    """Outbound representation for listing workspace API key metadata."""

    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str
    name: str
    masked_key: str
    is_active: bool
    created_at: str


class DisableApiKeyResponse(BaseModel):
    """Outbound payload confirming key disable state transition."""

    model_config = ConfigDict(extra="forbid")

    id: str
    is_active: bool


class ApiKeyControllerFactory:
    """Compose API-key management routes with auth-aware workspace checks.

    Architectural role:
    - Inbound compatibility adapter that enforces request-level ownership rules
      while delegating key operations to repositories/services.
    """

    def __init__(self) -> None:
        """Initialize concrete repositories and auth service dependencies."""

        self._api_key_repository = PostgresApiKeyRepository()
        self._workspace_repository = PostgresWorkspaceRepository()
        self._audit_logger = AuditLogger(audit_log_repository=PostgresAuditLogRepository())
        self._auth_service = AuthService(api_key_repository=self._api_key_repository)

    def build(self) -> APIRouter:
        """Build router exposing create/list/disable API key endpoints."""

        router = APIRouter(tags=["api-keys"])

        @router.post(
            "/workspaces/{workspace_id}/api-keys",
            response_model=CreateApiKeyResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_api_key(
            workspace_id: str,
            request: CreateApiKeyRequest,
            auth: AuthContext = Depends(require_auth),
        ) -> CreateApiKeyResponse:
            """Create and persist a new API key for authenticated workspace.

            Args:
                workspace_id: Target workspace from URL path.
                request: Payload containing human-readable key name.
                auth: Authenticated principal injected from auth dependency.

            Returns:
                CreateApiKeyResponse: One-time raw key material plus stored name.

            Internal flow:
            - Enforce same-workspace ownership from auth context.
            - Validate workspace existence.
            - Generate raw key, hash for storage, and persist hash only.
            """

            if auth.workspace_id != workspace_id:
                raise HTTPException(status_code=403, detail="workspace access denied")

            workspace = await self._workspace_repository.get_by_id(workspace_id)
            if workspace is None:
                raise HTTPException(status_code=404, detail="workspace not found")

            raw_api_key = self._auth_service.generate_api_key()
            key_hash = self._auth_service.hash_api_key(raw_api_key)
            name = request.name.strip()
            if not name:
                raise HTTPException(status_code=400, detail="name is required")

            created = await self._api_key_repository.create(workspace_id=workspace_id, key_hash=key_hash, name=name)
            await self._audit_logger.log(
                actor_id=None,
                action="api_key.create",
                resource="api_key",
                resource_id=created.id,
                before=None,
                after={
                    "id": created.id,
                    "workspace_id": created.workspace_id,
                    "name": created.name,
                    "is_active": created.is_active,
                },
                metadata={
                    "source": "api_key_controller",
                    "workspace_id": auth.workspace_id,
                    "auth_api_key_id": auth.api_key_id,
                },
            )
            return CreateApiKeyResponse(api_key=raw_api_key, name=name)

        @router.get("/workspaces/{workspace_id}/api-keys", response_model=list[ApiKeyResponse])
        async def list_api_keys(
            workspace_id: str,
            auth: AuthContext = Depends(require_auth),
        ) -> list[ApiKeyResponse]:
            """List API keys for the authenticated workspace.

            Args:
                workspace_id: Target workspace from URL path.
                auth: Authenticated principal.

            Returns:
                list[ApiKeyResponse]: Key metadata list with masked key field.
            """

            if auth.workspace_id != workspace_id:
                raise HTTPException(status_code=403, detail="workspace access denied")

            workspace = await self._workspace_repository.get_by_id(workspace_id)
            if workspace is None:
                raise HTTPException(status_code=404, detail="workspace not found")

            api_keys = await self._api_key_repository.list_by_workspace(workspace_id)
            return [
                ApiKeyResponse(
                    id=api_key.id,
                    workspace_id=api_key.workspace_id,
                    name=api_key.name,
                    masked_key="notiq_****",
                    is_active=api_key.is_active,
                    created_at=api_key.created_at.isoformat(),
                )
                for api_key in api_keys
            ]

        @router.patch("/api-keys/{api_key_id}/disable", response_model=DisableApiKeyResponse)
        async def disable_api_key(
            api_key_id: str,
            auth: AuthContext = Depends(require_auth),
        ) -> DisableApiKeyResponse:
            """Disable an API key if it belongs to the authenticated workspace.

            Args:
                api_key_id: API key identifier from URL path.
                auth: Authenticated principal for ownership enforcement.

            Returns:
                DisableApiKeyResponse: Disable confirmation payload.

            Edge cases:
            - Missing key returns 404.
            - Cross-workspace access returns 403.
            """

            api_key = await self._api_key_repository.get_by_id(api_key_id)
            if api_key is None:
                raise HTTPException(status_code=404, detail="api key not found")

            if api_key.workspace_id != auth.workspace_id:
                raise HTTPException(status_code=403, detail="workspace access denied")

            before_state = {
                "id": api_key.id,
                "workspace_id": api_key.workspace_id,
                "name": api_key.name,
                "is_active": api_key.is_active,
            }
            disabled = await self._api_key_repository.disable(api_key_id)
            if disabled is None:
                raise HTTPException(status_code=404, detail="api key not found")

            await self._audit_logger.log(
                actor_id=None,
                action="api_key.revoke",
                resource="api_key",
                resource_id=disabled.id,
                before=before_state,
                after={
                    "id": disabled.id,
                    "workspace_id": disabled.workspace_id,
                    "name": disabled.name,
                    "is_active": disabled.is_active,
                },
                metadata={
                    "source": "api_key_controller",
                    "workspace_id": auth.workspace_id,
                    "auth_api_key_id": auth.api_key_id,
                },
            )

            return DisableApiKeyResponse(id=disabled.id, is_active=disabled.is_active)

        return router

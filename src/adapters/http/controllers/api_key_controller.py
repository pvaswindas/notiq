from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from src.adapters.http.dependencies.auth import AuthContext, require_auth
from src.application.services.auth_service import AuthService
from src.infrastructure.database.repositories.postgres_api_key_repository import PostgresApiKeyRepository
from src.infrastructure.database.repositories.postgres_workspace_repository import PostgresWorkspaceRepository


class CreateApiKeyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)


class CreateApiKeyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_key: str
    name: str


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str
    name: str
    masked_key: str
    is_active: bool
    created_at: str


class DisableApiKeyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    is_active: bool


class ApiKeyControllerFactory:
    def __init__(self) -> None:
        self._api_key_repository = PostgresApiKeyRepository()
        self._workspace_repository = PostgresWorkspaceRepository()
        self._auth_service = AuthService(api_key_repository=self._api_key_repository)

    def build(self) -> APIRouter:
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

            await self._api_key_repository.create(workspace_id=workspace_id, key_hash=key_hash, name=name)
            return CreateApiKeyResponse(api_key=raw_api_key, name=name)

        @router.get("/workspaces/{workspace_id}/api-keys", response_model=list[ApiKeyResponse])
        async def list_api_keys(
            workspace_id: str,
            auth: AuthContext = Depends(require_auth),
        ) -> list[ApiKeyResponse]:
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
            api_key = await self._api_key_repository.get_by_id(api_key_id)
            if api_key is None:
                raise HTTPException(status_code=404, detail="api key not found")

            if api_key.workspace_id != auth.workspace_id:
                raise HTTPException(status_code=403, detail="workspace access denied")

            disabled = await self._api_key_repository.disable(api_key_id)
            if disabled is None:
                raise HTTPException(status_code=404, detail="api key not found")

            return DisableApiKeyResponse(id=disabled.id, is_active=disabled.is_active)

        return router

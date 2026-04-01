from dataclasses import dataclass

from fastapi import Depends, Request

from src.application.services.auth_service import AuthService, AuthenticatedPrincipal
from src.infrastructure.database.repositories.postgres_api_key_repository import PostgresApiKeyRepository


@dataclass(slots=True, frozen=True)
class AuthContext:
    workspace_id: str
    api_key_id: str


def get_auth_service() -> AuthService:
    return AuthService(api_key_repository=PostgresApiKeyRepository())


async def require_auth(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthContext:
    principal: AuthenticatedPrincipal = await auth_service.authenticate_request(request)
    request.state.workspace_id = principal.workspace_id
    request.state.api_key_id = principal.api_key_id
    return AuthContext(workspace_id=principal.workspace_id, api_key_id=principal.api_key_id)

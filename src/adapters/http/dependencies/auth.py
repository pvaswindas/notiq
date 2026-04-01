from dataclasses import dataclass

from fastapi import Depends, Request

from src.application.services.auth_service import AuthService, AuthenticatedPrincipal
from src.infrastructure.database.repositories.postgres_api_key_repository import PostgresApiKeyRepository


@dataclass(slots=True, frozen=True)
class AuthContext:
    """Request-scoped authenticated principal projected for route handlers.

    Purpose:
    - Carry workspace and API key identity derived from bearer authentication.
    """

    workspace_id: str
    api_key_id: str


def get_auth_service() -> AuthService:
    """Create auth service bound to concrete API-key repository adapter.

    Returns:
        AuthService: Service used by dependency-injected authentication flow.
    """

    return AuthService(api_key_repository=PostgresApiKeyRepository())


async def require_auth(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthContext:
    """Authenticate request and expose workspace-scoped auth context.

    Args:
        request: Incoming FastAPI request containing authorization header.
        auth_service: Injected service responsible for key validation.

    Returns:
        AuthContext: Workspace and API key ids for downstream ownership checks.

    Internal flow:
    - Validate bearer token and resolve principal.
    - Store principal metadata on request state for observability/debug access.
    """

    principal: AuthenticatedPrincipal = await auth_service.authenticate_request(request)
    request.state.workspace_id = principal.workspace_id
    request.state.api_key_id = principal.api_key_id
    return AuthContext(workspace_id=principal.workspace_id, api_key_id=principal.api_key_id)

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.services.auth_service import AdminAuthService
from src.application.services.rbac_service import RbacService
from src.infrastructure.database.repositories.postgres_admin_repository import PostgresAdminRepository
from src.infrastructure.database.repositories.postgres_permission_repository import PostgresPermissionRepository
from src.infrastructure.database.repositories.postgres_role_repository import PostgresRoleRepository


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(slots=True, frozen=True)
class AdminAuthContext:
    admin_id: str
    roles: tuple[str, ...]


def get_admin_auth_service() -> AdminAuthService:
    admin_repository = PostgresAdminRepository()
    role_repository = PostgresRoleRepository()
    return AdminAuthService(admin_repository=admin_repository, role_repository=role_repository)


def get_rbac_service() -> RbacService:
    return RbacService(
        admin_repository=PostgresAdminRepository(),
        permission_repository=PostgresPermissionRepository(),
    )


async def require_admin_auth(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_service: Annotated[AdminAuthService, Depends(get_admin_auth_service)],
) -> AdminAuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing admin bearer token")

    claims = auth_service.decode_access_token(credentials.credentials)
    request.state.admin_id = claims.admin_id
    return AdminAuthContext(admin_id=claims.admin_id, roles=claims.roles)


def require_permission(permission_name: str):
    async def dependency(
        auth: Annotated[AdminAuthContext, Depends(require_admin_auth)],
        rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
    ) -> AdminAuthContext:
        has_access = await rbac_service.has_permission(auth.admin_id, permission_name)
        if not has_access:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient permissions")
        return auth

    return dependency

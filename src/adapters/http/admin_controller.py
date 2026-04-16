from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError

from src.adapters.http.dependencies.admin_auth import (
    AdminAuthContext,
    require_admin_auth,
    require_permission,
)
from src.application.admin_use_cases.assign_role import AssignRoleInput, AssignRoleUseCase
from src.application.admin_use_cases.create_admin import CreateAdminInput, CreateAdminUseCase
from src.application.admin_use_cases.login_admin import LoginAdminInput, LoginAdminUseCase
from src.application.services.audit_logger import AuditLogger
from src.application.services.auth_service import AdminAuthService
from src.application.use_cases.disable_workspace import DisableWorkspaceInput, DisableWorkspaceUseCase
from src.domain.rate_limit.entities import RateLimitConfig
from src.infrastructure.database.repositories.postgres_audit_log_repository import PostgresAuditLogRepository
from src.infrastructure.database.repositories.postgres_admin_repository import PostgresAdminRepository
from src.infrastructure.database.repositories.postgres_permission_repository import PostgresPermissionRepository
from src.infrastructure.database.repositories.postgres_rate_limit_config_repository import PostgresRateLimitConfigRepository
from src.infrastructure.database.repositories.postgres_role_repository import PostgresRoleRepository
from src.infrastructure.database.repositories.postgres_workspace_repository import PostgresWorkspaceRepository


class LoginRequest(BaseModel):
    """Inbound payload for admin sign-in.

    Purpose:
    - Capture credential input required to mint an admin access token.
    """

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    """Outbound contract returned after successful admin authentication.

    Architectural role:
    - Stable transport DTO containing token metadata and resolved role names.
    """

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str
    expires_at: str
    admin_id: str
    roles: list[str]


class CreateAdminRequest(BaseModel):
    """Inbound payload for creating a new administrative identity."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=256)
    role_ids: list[str] = Field(default_factory=list)


class AdminResponse(BaseModel):
    """Common outbound projection for admin resources in management endpoints."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    email: str
    is_active: bool
    created_at: str
    roles: list[str]


class AdminProfileResponse(BaseModel):
    """Outbound projection for `/admin/me` including effective permissions."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    email: str
    is_active: bool
    created_at: str
    roles: list[str]
    permissions: list[str]


class AssignRoleRequest(BaseModel):
    """Inbound payload for assigning one role to an admin."""

    model_config = ConfigDict(extra="forbid")

    role_id: str = Field(min_length=1)


class RoleRequest(BaseModel):
    """Inbound payload for role creation requests."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)


class PermissionRequest(BaseModel):
    """Inbound payload for permission creation requests."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)


class RoleResponse(BaseModel):
    """Outbound representation of an RBAC role resource."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    created_at: str


class PermissionResponse(BaseModel):
    """Outbound representation of an RBAC permission resource."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    created_at: str


class AssignPermissionRequest(BaseModel):
    """Inbound payload for assigning one permission to a role."""

    model_config = ConfigDict(extra="forbid")

    permission_id: str = Field(min_length=1)


class DisableWorkspaceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    is_active: bool
    created_at: str


class CreateRateLimitConfigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str | None = None
    scope: str = Field(min_length=1, max_length=16)
    key: str = Field(min_length=1, max_length=128)
    limit: int = Field(gt=0)
    window_seconds: int = Field(gt=0)


class UpdateRateLimitConfigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str | None = None
    scope: str = Field(min_length=1, max_length=16)
    key: str = Field(min_length=1, max_length=128)
    limit: int = Field(gt=0)
    window_seconds: int = Field(gt=0)


class RateLimitConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str | None
    scope: str
    key: str
    limit: int
    window_seconds: int


class AdminControllerFactory:
    """Compose admin authentication and RBAC HTTP endpoints.

    Responsibilities:
    - Validate protocol-level request contracts.
    - Enforce authentication and permission dependencies.
    - Delegate business decisions to admin use cases and services.
    """

    def __init__(self) -> None:
        """Initialize concrete repositories, auth services, and admin use cases.

        Important:
        - This is a compatibility composition point; domain policy must remain in
          application services/use cases rather than route handlers.
        """

        self._admin_repository = PostgresAdminRepository()
        self._role_repository = PostgresRoleRepository()
        self._permission_repository = PostgresPermissionRepository()
        self._workspace_repository = PostgresWorkspaceRepository()
        self._rate_limit_config_repository = PostgresRateLimitConfigRepository()
        self._audit_log_repository = PostgresAuditLogRepository()
        self._audit_logger = AuditLogger(audit_log_repository=self._audit_log_repository)

        self._admin_auth_service = AdminAuthService(
            admin_repository=self._admin_repository,
            role_repository=self._role_repository,
        )
        self._create_admin_use_case = CreateAdminUseCase(
            admin_repository=self._admin_repository,
            role_repository=self._role_repository,
            auth_service=self._admin_auth_service,
            audit_logger=self._audit_logger,
        )
        self._login_admin_use_case = LoginAdminUseCase(auth_service=self._admin_auth_service)
        self._assign_role_use_case = AssignRoleUseCase(
            admin_repository=self._admin_repository,
            role_repository=self._role_repository,
            audit_logger=self._audit_logger,
        )
        self._disable_workspace_use_case = DisableWorkspaceUseCase(
            workspace_repository=self._workspace_repository,
            audit_logger=self._audit_logger,
        )

    def build(self) -> APIRouter:
        """Build and return the `/admin` router with RBAC-aware endpoints.

        Returns:
            APIRouter: Router exposing login, profile, admin, role, and
                permission management routes.
        """

        router = APIRouter(prefix="/admin", tags=["admin"])

        def _normalize_scope(scope_value: str) -> str:
            normalized = scope_value.strip().lower()
            if normalized not in {"group", "provider", "tenant", "global", "channel"}:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid rate limit scope")
            return normalized

        @router.post("/auth/login", response_model=LoginResponse)
        async def login(payload: LoginRequest) -> LoginResponse:
            """Authenticate an admin and return a signed access token.

            Args:
                payload: Login credentials payload.

            Returns:
                LoginResponse: Access token details and caller identity metadata.

            Internal flow:
            - Normalize and validate credentials in login use case/service.
            - Resolve assigned role names.
            - Return token expiry and role claims for downstream authorization.
            """

            result = await self._login_admin_use_case.execute(
                LoginAdminInput(email=payload.email, password=payload.password)
            )
            return LoginResponse(
                access_token=result.access_token,
                token_type=result.token_type,
                expires_at=result.expires_at.isoformat(),
                admin_id=result.admin.id,
                roles=list(result.roles),
            )

        @router.get("/me", response_model=AdminProfileResponse)
        async def me(auth: Annotated[AdminAuthContext, Depends(require_admin_auth)]) -> AdminProfileResponse:
            """Return profile details for the authenticated admin principal.

            Args:
                auth: Decoded admin auth context from JWT dependency.

            Returns:
                AdminProfileResponse: Admin identity plus roles and permissions.

            Edge cases:
            - Missing admin record after token decode returns `404`.
            """

            admin = await self._admin_repository.get_by_id(auth.admin_id)
            if admin is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="admin not found")

            roles = await self._role_repository.list_by_admin(admin.id)
            permissions = await self._permission_repository.list_by_admin(admin.id)
            return AdminProfileResponse(
                id=admin.id,
                name=admin.name,
                email=admin.email,
                is_active=admin.is_active,
                created_at=admin.created_at.isoformat(),
                roles=[role.name for role in roles],
                permissions=[permission.name for permission in permissions],
            )

        @router.post(
            "/admins",
            response_model=AdminResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_admin(
            payload: CreateAdminRequest,
            auth: Annotated[AdminAuthContext, Depends(require_permission("manage_admins"))],
        ) -> AdminResponse:
            """Create a new admin and optionally assign initial roles.

            Args:
                payload: New admin identity plus optional role ids.

            Returns:
                AdminResponse: Created admin with resolved role names.

            Edge cases:
            - Duplicate email maps to `409`.
            - Unknown role ids map to `404` from use case.
            """

            try:
                admin = await self._create_admin_use_case.execute(
                    CreateAdminInput(
                        name=payload.name,
                        email=payload.email,
                        password=payload.password,
                        role_ids=tuple(payload.role_ids),
                        actor_id=auth.admin_id,
                    )
                )
            except IntegrityError as exc:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="admin email already exists") from exc

            roles = await self._role_repository.list_by_admin(admin.id)
            return AdminResponse(
                id=admin.id,
                name=admin.name,
                email=admin.email,
                is_active=admin.is_active,
                created_at=admin.created_at.isoformat(),
                roles=[role.name for role in roles],
            )

        @router.get(
            "/admins",
            response_model=list[AdminResponse],
            dependencies=[Depends(require_permission("manage_admins"))],
        )
        async def list_admins() -> list[AdminResponse]:
            """List all admins including their role memberships.

            Returns:
                list[AdminResponse]: Admin records enriched with role names.

            Internal flow:
            - Load admin records.
            - Resolve roles per admin for a management-friendly view.
            """

            admins = await self._admin_repository.list_all()
            response: list[AdminResponse] = []
            for admin in admins:
                roles = await self._role_repository.list_by_admin(admin.id)
                response.append(
                    AdminResponse(
                        id=admin.id,
                        name=admin.name,
                        email=admin.email,
                        is_active=admin.is_active,
                        created_at=admin.created_at.isoformat(),
                        roles=[role.name for role in roles],
                    )
                )
            return response

        @router.post(
            "/admins/{admin_id}/roles",
            status_code=status.HTTP_204_NO_CONTENT,
        )
        async def assign_role(
            admin_id: str,
            payload: AssignRoleRequest,
            auth: Annotated[AdminAuthContext, Depends(require_permission("manage_admins"))],
        ) -> None:
            """Assign a role to an admin.

            Args:
                admin_id: Target admin identifier.
                payload: Role assignment payload.

            Returns:
                None: Route returns HTTP `204 No Content` on success.

            Edge cases:
            - Unknown admin/role ids map to `404`.
            """

            await self._assign_role_use_case.execute(
                AssignRoleInput(
                    admin_id=admin_id,
                    role_id=payload.role_id,
                    actor_id=auth.admin_id,
                )
            )

        @router.patch(
            "/admins/{admin_id}/disable",
            response_model=AdminResponse,
        )
        async def disable_admin(
            admin_id: str,
            auth: Annotated[AdminAuthContext, Depends(require_permission("manage_admins"))],
        ) -> AdminResponse:
            """Disable an admin account and return the updated representation.

            Args:
                admin_id: Target admin identifier.

            Returns:
                AdminResponse: Updated admin state with `is_active=false`.

            Edge cases:
            - Missing admin returns `404`.
            """

            before_admin = await self._admin_repository.get_by_id(admin_id)
            if before_admin is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="admin not found")
            admin = await self._admin_repository.set_active(admin_id, False)
            if admin is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="admin not found")

            await self._audit_logger.log(
                actor_id=auth.admin_id,
                action="admin.disable",
                resource="admin",
                resource_id=admin.id,
                before={
                    "id": before_admin.id,
                    "name": before_admin.name,
                    "email": before_admin.email,
                    "is_active": before_admin.is_active,
                },
                after={
                    "id": admin.id,
                    "name": admin.name,
                    "email": admin.email,
                    "is_active": admin.is_active,
                },
            )

            roles = await self._role_repository.list_by_admin(admin.id)
            return AdminResponse(
                id=admin.id,
                name=admin.name,
                email=admin.email,
                is_active=admin.is_active,
                created_at=admin.created_at.isoformat(),
                roles=[role.name for role in roles],
            )

        @router.post(
            "/roles",
            response_model=RoleResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_role(
            payload: RoleRequest,
            auth: Annotated[AdminAuthContext, Depends(require_permission("manage_roles"))],
        ) -> RoleResponse:
            """Create a new RBAC role.

            Args:
                payload: Role creation request.

            Returns:
                RoleResponse: Persisted role metadata.

            Edge cases:
            - Blank/duplicate names map to `400` or `409`.
            """

            name = payload.name.strip()
            if not name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name is required")

            existing = await self._role_repository.get_by_name(name)
            if existing is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="role already exists")

            try:
                role = await self._role_repository.create(name=name)
            except IntegrityError as exc:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="role already exists") from exc

            await self._audit_logger.log(
                actor_id=auth.admin_id,
                action="role.create",
                resource="role",
                resource_id=role.id,
                before=None,
                after={"id": role.id, "name": role.name},
            )
            return RoleResponse(id=role.id, name=role.name, created_at=role.created_at.isoformat())

        @router.get(
            "/roles",
            response_model=list[RoleResponse],
            dependencies=[Depends(require_admin_auth)],
        )
        async def list_roles() -> list[RoleResponse]:
            """List all roles available for RBAC assignment.

            Returns:
                list[RoleResponse]: Role records in repository order.
            """

            roles = await self._role_repository.list_all()
            return [RoleResponse(id=role.id, name=role.name, created_at=role.created_at.isoformat()) for role in roles]

        @router.post(
            "/permissions",
            response_model=PermissionResponse,
            status_code=status.HTTP_201_CREATED,
            dependencies=[Depends(require_permission("manage_permissions"))],
        )
        async def create_permission(payload: PermissionRequest) -> PermissionResponse:
            """Create a new RBAC permission.

            Args:
                payload: Permission creation request.

            Returns:
                PermissionResponse: Persisted permission metadata.

            Edge cases:
            - Blank/duplicate names map to `400` or `409`.
            """

            name = payload.name.strip()
            if not name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name is required")

            existing = await self._permission_repository.get_by_name(name)
            if existing is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="permission already exists")

            try:
                permission = await self._permission_repository.create(name=name)
            except IntegrityError as exc:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="permission already exists") from exc
            return PermissionResponse(
                id=permission.id,
                name=permission.name,
                created_at=permission.created_at.isoformat(),
            )

        @router.get(
            "/permissions",
            response_model=list[PermissionResponse],
            dependencies=[Depends(require_admin_auth)],
        )
        async def list_permissions() -> list[PermissionResponse]:
            """List all known RBAC permissions.

            Returns:
                list[PermissionResponse]: Permission records in repository order.
            """

            permissions = await self._permission_repository.list_all()
            return [
                PermissionResponse(
                    id=permission.id,
                    name=permission.name,
                    created_at=permission.created_at.isoformat(),
                )
                for permission in permissions
            ]

        @router.patch(
            "/workspaces/{workspace_id}/disable",
            response_model=DisableWorkspaceResponse,
        )
        async def disable_workspace(
            workspace_id: str,
            auth: Annotated[AdminAuthContext, Depends(require_permission("manage_workspaces"))],
        ) -> DisableWorkspaceResponse:
            try:
                workspace = await self._disable_workspace_use_case.execute(
                    DisableWorkspaceInput(
                        workspace_id=workspace_id,
                        actor_id=auth.admin_id,
                        audit_metadata={"source": "admin"},
                    )
                )
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

            return DisableWorkspaceResponse(
                id=workspace.id,
                name=workspace.name,
                is_active=workspace.is_active,
                created_at=workspace.created_at.isoformat(),
            )

        @router.post(
            "/rate-limit-configs",
            response_model=RateLimitConfigResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_rate_limit_config(
            payload: CreateRateLimitConfigRequest,
            auth: Annotated[AdminAuthContext, Depends(require_permission("manage_rate_limits"))],
        ) -> RateLimitConfigResponse:
            scope = _normalize_scope(payload.scope)
            key = payload.key.strip()
            if not key:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="key is required")
            workspace_id = payload.workspace_id.strip() if isinstance(payload.workspace_id, str) else None

            config = RateLimitConfig(
                id=f"rlc_{uuid4().hex[:24]}",
                workspace_id=workspace_id,
                scope=scope,  # type: ignore[arg-type,assignment]
                key=key,
                limit=payload.limit,
                window_seconds=payload.window_seconds,
            )
            saved = await self._rate_limit_config_repository.save(config)
            await self._audit_logger.log(
                actor_id=auth.admin_id,
                action="rate_limit.create",
                resource="rate_limit_config",
                resource_id=saved.id or "",
                before=None,
                after={
                    "id": saved.id,
                    "workspace_id": saved.workspace_id,
                    "scope": saved.scope,
                    "key": saved.key,
                    "limit": saved.limit,
                    "window_seconds": saved.window_seconds,
                },
            )
            return RateLimitConfigResponse(
                id=saved.id or "",
                workspace_id=saved.workspace_id,
                scope=saved.scope,
                key=saved.key,
                limit=saved.limit,
                window_seconds=saved.window_seconds,
            )

        @router.put(
            "/rate-limit-configs/{config_id}",
            response_model=RateLimitConfigResponse,
        )
        async def update_rate_limit_config(
            config_id: str,
            payload: UpdateRateLimitConfigRequest,
            auth: Annotated[AdminAuthContext, Depends(require_permission("manage_rate_limits"))],
        ) -> RateLimitConfigResponse:
            workspace_id = payload.workspace_id.strip() if isinstance(payload.workspace_id, str) else ""
            before_config = await self._rate_limit_config_repository.get_by_id(config_id=config_id, workspace_id=workspace_id)
            if before_config is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rate limit config not found")
            normalized_key = payload.key.strip()
            if not normalized_key:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="key is required")

            updated = await self._rate_limit_config_repository.update(
                RateLimitConfig(
                    id=config_id,
                    workspace_id=payload.workspace_id.strip() if isinstance(payload.workspace_id, str) else None,
                    scope=_normalize_scope(payload.scope),  # type: ignore[arg-type,assignment]
                    key=normalized_key,
                    limit=payload.limit,
                    window_seconds=payload.window_seconds,
                )
            )
            await self._audit_logger.log(
                actor_id=auth.admin_id,
                action="rate_limit.update",
                resource="rate_limit_config",
                resource_id=config_id,
                before={
                    "id": before_config.id,
                    "workspace_id": before_config.workspace_id,
                    "scope": before_config.scope,
                    "key": before_config.key,
                    "limit": before_config.limit,
                    "window_seconds": before_config.window_seconds,
                },
                after={
                    "id": updated.id,
                    "workspace_id": updated.workspace_id,
                    "scope": updated.scope,
                    "key": updated.key,
                    "limit": updated.limit,
                    "window_seconds": updated.window_seconds,
                },
            )
            return RateLimitConfigResponse(
                id=updated.id or "",
                workspace_id=updated.workspace_id,
                scope=updated.scope,
                key=updated.key,
                limit=updated.limit,
                window_seconds=updated.window_seconds,
            )

        @router.delete("/rate-limit-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete_rate_limit_config(
            config_id: str,
            auth: Annotated[AdminAuthContext, Depends(require_permission("manage_rate_limits"))],
            workspace_id: str | None = None,
        ) -> None:
            scoped_workspace_id = workspace_id.strip() if isinstance(workspace_id, str) else ""
            before_config = await self._rate_limit_config_repository.get_by_id(
                config_id=config_id,
                workspace_id=scoped_workspace_id,
            )
            if before_config is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rate limit config not found")

            deleted = await self._rate_limit_config_repository.delete(
                config_id=config_id,
                workspace_id=before_config.workspace_id,
            )
            if not deleted:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rate limit config not found")

            await self._audit_logger.log(
                actor_id=auth.admin_id if auth is not None else None,
                action="rate_limit.delete",
                resource="rate_limit_config",
                resource_id=config_id,
                before={
                    "id": before_config.id,
                    "workspace_id": before_config.workspace_id,
                    "scope": before_config.scope,
                    "key": before_config.key,
                    "limit": before_config.limit,
                    "window_seconds": before_config.window_seconds,
                },
                after=None,
            )

        @router.post(
            "/roles/{role_id}/permissions",
            status_code=status.HTTP_204_NO_CONTENT,
        )
        async def assign_permission(
            role_id: str,
            payload: AssignPermissionRequest,
            auth: Annotated[AdminAuthContext, Depends(require_permission("manage_roles"))],
        ) -> None:
            """Assign a permission to a role.

            Args:
                role_id: Target role identifier.
                payload: Permission assignment payload.

            Returns:
                None: Route returns HTTP `204 No Content` on success.

            Internal flow:
            - Validate role existence.
            - Validate permission existence.
            - Persist role-permission link.
            """

            role = await self._role_repository.get_by_id(role_id)
            if role is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="role not found")

            permission = await self._permission_repository.get_by_id(payload.permission_id)
            if permission is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="permission not found")

            before_permissions = await self._role_repository.list_permissions(role_id)
            await self._role_repository.assign_permission(role_id=role_id, permission_id=payload.permission_id)
            after_permissions = await self._role_repository.list_permissions(role_id)
            await self._audit_logger.log(
                actor_id=auth.admin_id,
                action="role.assign_permission",
                resource="role",
                resource_id=role_id,
                before={"permissions": [item.name for item in before_permissions]},
                after={"permissions": [item.name for item in after_permissions]},
                metadata={"permission_id": payload.permission_id, "permission_name": permission.name},
            )

        @router.get(
            "/roles/{role_id}/permissions",
            response_model=list[PermissionResponse],
            dependencies=[Depends(require_admin_auth)],
        )
        async def list_role_permissions(role_id: str) -> list[PermissionResponse]:
            """List permissions assigned to one role.

            Args:
                role_id: Target role identifier.

            Returns:
                list[PermissionResponse]: Permissions mapped to role.

            Edge cases:
            - Missing role returns `404`.
            """

            role = await self._role_repository.get_by_id(role_id)
            if role is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="role not found")

            permissions = await self._role_repository.list_permissions(role_id)
            return [
                PermissionResponse(
                    id=permission.id,
                    name=permission.name,
                    created_at=permission.created_at.isoformat(),
                )
                for permission in permissions
            ]

        return router

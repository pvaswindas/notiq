from typing import Annotated

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
from src.application.services.auth_service import AdminAuthService
from src.infrastructure.database.repositories.postgres_admin_repository import PostgresAdminRepository
from src.infrastructure.database.repositories.postgres_permission_repository import PostgresPermissionRepository
from src.infrastructure.database.repositories.postgres_role_repository import PostgresRoleRepository


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str
    expires_at: str
    admin_id: str
    roles: list[str]


class CreateAdminRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=256)
    role_ids: list[str] = Field(default_factory=list)


class AdminResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    email: str
    is_active: bool
    created_at: str
    roles: list[str]


class AdminProfileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    email: str
    is_active: bool
    created_at: str
    roles: list[str]
    permissions: list[str]


class AssignRoleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_id: str = Field(min_length=1)


class RoleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)


class PermissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)


class RoleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    created_at: str


class PermissionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    created_at: str


class AssignPermissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    permission_id: str = Field(min_length=1)


class AdminControllerFactory:
    def __init__(self) -> None:
        self._admin_repository = PostgresAdminRepository()
        self._role_repository = PostgresRoleRepository()
        self._permission_repository = PostgresPermissionRepository()

        self._admin_auth_service = AdminAuthService(
            admin_repository=self._admin_repository,
            role_repository=self._role_repository,
        )
        self._create_admin_use_case = CreateAdminUseCase(
            admin_repository=self._admin_repository,
            role_repository=self._role_repository,
            auth_service=self._admin_auth_service,
        )
        self._login_admin_use_case = LoginAdminUseCase(auth_service=self._admin_auth_service)
        self._assign_role_use_case = AssignRoleUseCase(
            admin_repository=self._admin_repository,
            role_repository=self._role_repository,
        )

    def build(self) -> APIRouter:
        router = APIRouter(prefix="/admin", tags=["admin"])

        @router.post("/auth/login", response_model=LoginResponse)
        async def login(payload: LoginRequest) -> LoginResponse:
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
            dependencies=[Depends(require_permission("manage_admins"))],
        )
        async def create_admin(payload: CreateAdminRequest) -> AdminResponse:
            try:
                admin = await self._create_admin_use_case.execute(
                    CreateAdminInput(
                        name=payload.name,
                        email=payload.email,
                        password=payload.password,
                        role_ids=tuple(payload.role_ids),
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
            dependencies=[Depends(require_permission("manage_admins"))],
        )
        async def assign_role(admin_id: str, payload: AssignRoleRequest) -> None:
            await self._assign_role_use_case.execute(AssignRoleInput(admin_id=admin_id, role_id=payload.role_id))

        @router.patch(
            "/admins/{admin_id}/disable",
            response_model=AdminResponse,
            dependencies=[Depends(require_permission("manage_admins"))],
        )
        async def disable_admin(admin_id: str) -> AdminResponse:
            admin = await self._admin_repository.set_active(admin_id, False)
            if admin is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="admin not found")

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
            dependencies=[Depends(require_permission("manage_roles"))],
        )
        async def create_role(payload: RoleRequest) -> RoleResponse:
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
            return RoleResponse(id=role.id, name=role.name, created_at=role.created_at.isoformat())

        @router.get(
            "/roles",
            response_model=list[RoleResponse],
            dependencies=[Depends(require_admin_auth)],
        )
        async def list_roles() -> list[RoleResponse]:
            roles = await self._role_repository.list_all()
            return [RoleResponse(id=role.id, name=role.name, created_at=role.created_at.isoformat()) for role in roles]

        @router.post(
            "/permissions",
            response_model=PermissionResponse,
            status_code=status.HTTP_201_CREATED,
            dependencies=[Depends(require_permission("manage_permissions"))],
        )
        async def create_permission(payload: PermissionRequest) -> PermissionResponse:
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
            permissions = await self._permission_repository.list_all()
            return [
                PermissionResponse(
                    id=permission.id,
                    name=permission.name,
                    created_at=permission.created_at.isoformat(),
                )
                for permission in permissions
            ]

        @router.post(
            "/roles/{role_id}/permissions",
            status_code=status.HTTP_204_NO_CONTENT,
            dependencies=[Depends(require_permission("manage_roles"))],
        )
        async def assign_permission(role_id: str, payload: AssignPermissionRequest) -> None:
            role = await self._role_repository.get_by_id(role_id)
            if role is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="role not found")

            permission = await self._permission_repository.get_by_id(payload.permission_id)
            if permission is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="permission not found")

            await self._role_repository.assign_permission(role_id=role_id, permission_id=payload.permission_id)

        @router.get(
            "/roles/{role_id}/permissions",
            response_model=list[PermissionResponse],
            dependencies=[Depends(require_admin_auth)],
        )
        async def list_role_permissions(role_id: str) -> list[PermissionResponse]:
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

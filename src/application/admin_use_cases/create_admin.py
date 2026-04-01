from dataclasses import dataclass

from fastapi import HTTPException, status

from src.application.services.auth_service import AdminAuthService
from src.domain.admin.entities import Admin
from src.ports.admin_repository import AdminRepository
from src.ports.role_repository import RoleRepository


@dataclass(slots=True, frozen=True)
class CreateAdminInput:
    """Input contract for creating an admin identity and optional role links."""

    name: str
    email: str
    password: str
    role_ids: tuple[str, ...]


class CreateAdminUseCase:
    """Create admin accounts while enforcing uniqueness and role validity.

    Architectural role:
    - Application-layer orchestrator that coordinates validation, password
      hashing, and persistence calls through repositories/services.
    """

    def __init__(
        self,
        admin_repository: AdminRepository,
        role_repository: RoleRepository,
        auth_service: AdminAuthService,
    ) -> None:
        """Store repositories and auth service used by create-admin flow."""

        self._admin_repository = admin_repository
        self._role_repository = role_repository
        self._auth_service = auth_service

    async def execute(self, dto: CreateAdminInput) -> Admin:
        """Create an admin and assign requested roles.

        Args:
            dto: Create-admin command payload.

        Returns:
            Admin: Newly persisted admin entity.

        Internal flow:
        - Normalize and validate required fields.
        - Ensure admin email is unique.
        - Validate all provided role ids exist.
        - Hash password, persist admin, then persist role links.

        Edge cases and constraints:
        - Raises `400` for missing required values.
        - Raises `404` when any requested role id is unknown.
        - Raises `409` when email already exists.
        - Must not store plaintext passwords.
        """

        name = dto.name.strip()
        email = dto.email.strip().lower()
        password = dto.password

        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name is required")
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email is required")
        if not password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="password is required")

        existing = await self._admin_repository.get_by_email(email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="admin email already exists")

        for role_id in dto.role_ids:
            role = await self._role_repository.get_by_id(role_id)
            if role is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"role not found: {role_id}")

        password_hash = self._auth_service.hash_password(password)
        admin = await self._admin_repository.create(name=name, email=email, password_hash=password_hash)

        for role_id in dto.role_ids:
            await self._admin_repository.assign_role(admin.id, role_id)

        return admin

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, Request, status
from jwt import InvalidTokenError

from src.bootstrap.settings import settings
from src.domain.admin.entities import Admin
from src.domain.auth.entities import ApiKey
from src.ports.admin_repository import AdminRepository
from src.ports.api_key_repository import ApiKeyRepository
from src.ports.role_repository import RoleRepository


@dataclass(slots=True, frozen=True)
class AuthenticatedPrincipal:
    workspace_id: str
    api_key_id: str


@dataclass(slots=True, frozen=True)
class AdminTokenClaims:
    admin_id: str
    roles: tuple[str, ...]
    exp: int


@dataclass(slots=True, frozen=True)
class AdminLoginResult:
    access_token: str
    token_type: str
    expires_at: datetime
    admin: Admin
    roles: tuple[str, ...]


class AuthService:
    def __init__(self, api_key_repository: ApiKeyRepository) -> None:
        self._api_key_repository = api_key_repository

    @staticmethod
    def generate_api_key() -> str:
        return f"notiq_{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    @staticmethod
    def mask_api_key(api_key: str) -> str:
        if len(api_key) <= 10:
            return "notiq_****"
        return f"{api_key[:8]}{'*' * (len(api_key) - 12)}{api_key[-4:]}"

    @staticmethod
    def extract_api_key_from_request(request: Request) -> str:
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing api key",
            )

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid authorization header",
            )

        api_key = token.strip()
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing api key",
            )
        return api_key

    async def authenticate_request(self, request: Request) -> AuthenticatedPrincipal:
        api_key = self.extract_api_key_from_request(request)
        key_hash = self.hash_api_key(api_key)

        key_record = await self._api_key_repository.get_by_key_hash(key_hash)
        if key_record is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="invalid api key",
            )

        self._assert_hash_matches(key_record, key_hash)

        if not key_record.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="api key is disabled",
            )

        return AuthenticatedPrincipal(workspace_id=key_record.workspace_id, api_key_id=key_record.id)

    @staticmethod
    def _assert_hash_matches(key_record: ApiKey, computed_hash: str) -> None:
        if not hmac.compare_digest(key_record.key_hash, computed_hash):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="invalid api key",
            )


class AdminAuthService:
    def __init__(
        self,
        admin_repository: AdminRepository,
        role_repository: RoleRepository,
    ) -> None:
        self._admin_repository = admin_repository
        self._role_repository = role_repository

    @staticmethod
    def hash_password(plain_password: str) -> str:
        password = plain_password.encode("utf-8")
        return bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))

    def create_access_token(self, admin_id: str, roles: tuple[str, ...]) -> tuple[str, datetime]:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.admin_jwt_exp_minutes)
        payload = {
            "admin_id": admin_id,
            "roles": list(roles),
            "exp": expires_at,
        }
        token = jwt.encode(payload, settings.admin_jwt_secret, algorithm=settings.admin_jwt_algorithm)
        return token, expires_at

    def decode_access_token(self, token: str) -> AdminTokenClaims:
        try:
            payload = jwt.decode(token, settings.admin_jwt_secret, algorithms=[settings.admin_jwt_algorithm])
        except InvalidTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc

        admin_id = str(payload.get("admin_id", "")).strip()
        if not admin_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")

        role_values = payload.get("roles", [])
        if not isinstance(role_values, list):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")

        roles = tuple(str(role).strip() for role in role_values if str(role).strip())
        exp = int(payload.get("exp", 0))
        return AdminTokenClaims(admin_id=admin_id, roles=roles, exp=exp)

    async def login(self, email: str, password: str) -> AdminLoginResult:
        normalized_email = email.strip().lower()
        if not normalized_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email is required")
        if not password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="password is required")

        admin = await self._admin_repository.get_by_email(normalized_email)
        if admin is None or not self.verify_password(password, admin.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

        if not admin.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin is disabled")

        roles = tuple(role.name for role in await self._role_repository.list_by_admin(admin.id))
        token, expires_at = self.create_access_token(admin.id, roles)
        return AdminLoginResult(
            access_token=token,
            token_type="bearer",
            expires_at=expires_at,
            admin=admin,
            roles=roles,
        )

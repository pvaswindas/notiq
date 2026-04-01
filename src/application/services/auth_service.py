from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from src.domain.auth.entities import ApiKey
from src.ports.api_key_repository import ApiKeyRepository


@dataclass(slots=True, frozen=True)
class AuthenticatedPrincipal:
    workspace_id: str
    api_key_id: str


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

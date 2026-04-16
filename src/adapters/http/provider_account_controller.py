from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from src.adapters.http.dependencies.auth import AuthContext, require_auth
from src.modules.notifications.application.use_cases.create_provider_account_use_case import (
    CreateProviderAccountCommand,
    CreateProviderAccountUseCase,
)
from src.modules.notifications.application.use_cases.get_provider_account_use_case import (
    GetProviderAccountCommand,
    GetProviderAccountUseCase,
)
from src.modules.notifications.application.use_cases.list_provider_accounts_use_case import (
    ListProviderAccountsCommand,
    ListProviderAccountsUseCase,
)
from src.modules.notifications.domain.entities.provider_account import ProviderAccount


class CreateProviderAccountRequest(BaseModel):
    """Inbound payload for creating a provider account."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    credentials: dict = Field(default_factory=dict)


class ProviderAccountResponse(BaseModel):
    """Transport-safe provider account response without credentials."""

    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str | None
    provider: str
    is_active: bool
    created_at: str


class ProviderAccountControllerFactory:
    """Compose authenticated provider account management routes."""

    def __init__(
        self,
        create_provider_account_use_case: CreateProviderAccountUseCase,
        list_provider_accounts_use_case: ListProviderAccountsUseCase,
        get_provider_account_use_case: GetProviderAccountUseCase,
    ) -> None:
        self._create_provider_account_use_case = create_provider_account_use_case
        self._list_provider_accounts_use_case = list_provider_accounts_use_case
        self._get_provider_account_use_case = get_provider_account_use_case

    def build(self) -> APIRouter:
        router = APIRouter(tags=["provider-accounts"])

        @router.post(
            "/provider-accounts",
            response_model=ProviderAccountResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_provider_account(
            request: CreateProviderAccountRequest,
            auth: AuthContext = Depends(require_auth),
        ) -> ProviderAccountResponse:
            _enforce_workspace_access(auth, request.workspace_id)
            try:
                provider_account = await self._create_provider_account_use_case.execute(
                    CreateProviderAccountCommand(
                        workspace_id=request.workspace_id,
                        provider=request.provider,
                        credentials=request.credentials,
                        actor_id=None,
                        audit_metadata={
                            "source": "provider_account_api",
                            "workspace_id": auth.workspace_id,
                            "auth_api_key_id": auth.api_key_id,
                        },
                    )
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            return _to_provider_account_response(provider_account)

        @router.get("/provider-accounts", response_model=list[ProviderAccountResponse])
        async def list_provider_accounts(
            workspace_id: str = Query(min_length=1),
            auth: AuthContext = Depends(require_auth),
        ) -> list[ProviderAccountResponse]:
            _enforce_workspace_access(auth, workspace_id)
            try:
                provider_accounts = await self._list_provider_accounts_use_case.execute(
                    ListProviderAccountsCommand(workspace_id=workspace_id)
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            return [_to_provider_account_response(provider_account) for provider_account in provider_accounts]

        @router.get("/provider-accounts/{provider_account_id}", response_model=ProviderAccountResponse)
        async def get_provider_account(
            provider_account_id: str,
            auth: AuthContext = Depends(require_auth),
        ) -> ProviderAccountResponse:
            try:
                provider_account = await self._get_provider_account_use_case.execute(
                    GetProviderAccountCommand(
                        provider_account_id=provider_account_id,
                        workspace_id=auth.workspace_id,
                    )
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except PermissionError as exc:
                raise HTTPException(status_code=403, detail=str(exc)) from exc
            return _to_provider_account_response(provider_account)

        return router


def _enforce_workspace_access(auth: AuthContext, workspace_id: str) -> None:
    if auth.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="workspace access denied")


def _to_provider_account_response(provider_account: ProviderAccount) -> ProviderAccountResponse:
    return ProviderAccountResponse(
        id=provider_account.provider_account_id,
        workspace_id=provider_account.workspace_id,
        provider=provider_account.provider_key,
        is_active=provider_account.is_active,
        created_at=provider_account.created_at.isoformat(),
    )

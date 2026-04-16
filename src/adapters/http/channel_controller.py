from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from src.adapters.http.dependencies.auth import AuthContext, require_auth
from src.modules.notifications.application.errors import ConflictError
from src.modules.notifications.application.use_cases.create_managed_channel_use_case import (
    CreateManagedChannelCommand,
    CreateManagedChannelUseCase,
)
from src.modules.notifications.application.use_cases.disable_managed_channel_use_case import (
    DisableManagedChannelCommand,
    DisableManagedChannelUseCase,
)
from src.modules.notifications.application.use_cases.list_managed_channels_use_case import (
    ListManagedChannelsCommand,
    ListManagedChannelsUseCase,
)
from src.modules.notifications.domain.entities.channel import Channel


class CreateChannelRequest(BaseModel):
    """Inbound payload for creating a provider-account-backed channel."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    provider_account_id: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class DisableChannelRequest(BaseModel):
    """Inbound payload for disabling a channel within a workspace."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1)


class ChannelResponse(BaseModel):
    """Transport-safe channel representation for management APIs."""

    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str
    provider: str
    provider_account_id: str | None
    destination: str
    metadata: dict[str, str]
    is_active: bool
    created_at: str


class ChannelControllerFactory:
    """Compose authenticated channel management routes."""

    def __init__(
        self,
        create_channel_use_case: CreateManagedChannelUseCase,
        list_channels_use_case: ListManagedChannelsUseCase,
        disable_channel_use_case: DisableManagedChannelUseCase,
    ) -> None:
        self._create_channel_use_case = create_channel_use_case
        self._list_channels_use_case = list_channels_use_case
        self._disable_channel_use_case = disable_channel_use_case

    def build(self) -> APIRouter:
        router = APIRouter(tags=["channels"])

        @router.post("/channels", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
        async def create_channel(
            request: CreateChannelRequest,
            auth: AuthContext = Depends(require_auth),
        ) -> ChannelResponse:
            _enforce_workspace_access(auth, request.workspace_id)
            try:
                channel = await self._create_channel_use_case.execute(
                    CreateManagedChannelCommand(
                        workspace_id=request.workspace_id,
                        provider=request.provider,
                        provider_account_id=request.provider_account_id,
                        destination=request.destination,
                        metadata=request.metadata,
                        actor_id=None,
                        audit_metadata={
                            "source": "channel_api",
                            "workspace_id": auth.workspace_id,
                            "auth_api_key_id": auth.api_key_id,
                        },
                    )
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except PermissionError as exc:
                raise HTTPException(status_code=403, detail=str(exc)) from exc
            except ConflictError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            return _to_channel_response(channel)

        @router.get("/channels", response_model=list[ChannelResponse])
        async def list_channels(
            workspace_id: str = Query(min_length=1),
            auth: AuthContext = Depends(require_auth),
        ) -> list[ChannelResponse]:
            _enforce_workspace_access(auth, workspace_id)
            try:
                channels = await self._list_channels_use_case.execute(
                    ListManagedChannelsCommand(workspace_id=workspace_id)
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            return [_to_channel_response(channel) for channel in channels]

        @router.patch("/channels/{channel_id}", response_model=ChannelResponse)
        async def disable_channel(
            channel_id: str,
            request: DisableChannelRequest,
            auth: AuthContext = Depends(require_auth),
        ) -> ChannelResponse:
            _enforce_workspace_access(auth, request.workspace_id)
            try:
                channel = await self._disable_channel_use_case.execute(
                    DisableManagedChannelCommand(
                        channel_id=channel_id,
                        workspace_id=request.workspace_id,
                        actor_id=None,
                        audit_metadata={
                            "source": "channel_api",
                            "workspace_id": auth.workspace_id,
                            "auth_api_key_id": auth.api_key_id,
                        },
                    )
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            return _to_channel_response(channel)

        return router


def _enforce_workspace_access(auth: AuthContext, workspace_id: str) -> None:
    if auth.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="workspace access denied")


def _to_channel_response(channel: Channel) -> ChannelResponse:
    return ChannelResponse(
        id=channel.channel_id,
        workspace_id=channel.workspace_id,
        provider=channel.provider_key,
        provider_account_id=channel.provider_account_id,
        destination=channel.destination,
        metadata=dict(channel.metadata),
        is_active=channel.is_active,
        created_at=channel.created_at.isoformat(),
    )

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from src.application.use_cases.create_channel import CreateChannelInput, CreateChannelUseCase
from src.application.use_cases.disable_channel import DisableChannelInput, DisableChannelUseCase
from src.application.use_cases.list_channels import ListChannelsInput, ListChannelsUseCase
from src.application.use_cases.update_channel import UpdateChannelInput, UpdateChannelUseCase
from src.domain.entities.channel import Channel


class CreateChannelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)
    group: str | None = None
    is_active: bool = True


class UpdateChannelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)
    group: str | None = None
    is_active: bool = True


class DisableChannelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1)


class ChannelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str
    provider: str
    config: dict[str, Any]
    group: str | None
    is_active: bool


class ChannelControllerFactory:
    def __init__(
        self,
        create_channel_use_case: CreateChannelUseCase,
        list_channels_use_case: ListChannelsUseCase,
        update_channel_use_case: UpdateChannelUseCase,
        disable_channel_use_case: DisableChannelUseCase,
    ) -> None:
        self._create_channel_use_case = create_channel_use_case
        self._list_channels_use_case = list_channels_use_case
        self._update_channel_use_case = update_channel_use_case
        self._disable_channel_use_case = disable_channel_use_case

    def build(self) -> APIRouter:
        router = APIRouter(tags=["channels"])

        @router.post(
            "/workspaces/{workspace_id}/channels",
            response_model=ChannelResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_channel(workspace_id: str, request: CreateChannelRequest) -> ChannelResponse:
            try:
                channel = await self._create_channel_use_case.execute(
                    CreateChannelInput(
                        workspace_id=workspace_id,
                        provider=request.provider,
                        config=request.config,
                        group=request.group,
                        is_active=request.is_active,
                    )
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc

            return _to_channel_response(channel)

        @router.get("/workspaces/{workspace_id}/channels", response_model=list[ChannelResponse])
        async def list_channels(workspace_id: str) -> list[ChannelResponse]:
            try:
                channels = await self._list_channels_use_case.execute(
                    ListChannelsInput(workspace_id=workspace_id)
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc

            return [_to_channel_response(channel) for channel in channels]

        @router.put("/channels/{channel_id}", response_model=ChannelResponse)
        async def update_channel(channel_id: str, request: UpdateChannelRequest) -> ChannelResponse:
            try:
                channel = await self._update_channel_use_case.execute(
                    UpdateChannelInput(
                        channel_id=channel_id,
                        workspace_id=request.workspace_id,
                        provider=request.provider,
                        config=request.config,
                        group=request.group,
                        is_active=request.is_active,
                    )
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc

            return _to_channel_response(channel)

        @router.patch("/channels/{channel_id}/disable", response_model=ChannelResponse)
        async def disable_channel(channel_id: str, request: DisableChannelRequest) -> ChannelResponse:
            try:
                channel = await self._disable_channel_use_case.execute(
                    DisableChannelInput(
                        channel_id=channel_id,
                        workspace_id=request.workspace_id,
                    )
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc

            return _to_channel_response(channel)

        return router


def _to_channel_response(channel: Channel) -> ChannelResponse:
    return ChannelResponse(
        id=channel.id,
        workspace_id=channel.workspace_id,
        provider=channel.provider,
        config=channel.config,
        group=channel.group,
        is_active=channel.is_active,
    )

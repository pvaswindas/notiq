from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from src.application.use_cases.create_channel import CreateChannelInput, CreateChannelUseCase
from src.application.use_cases.disable_channel import DisableChannelInput, DisableChannelUseCase
from src.application.use_cases.list_channels import ListChannelsInput, ListChannelsUseCase
from src.application.use_cases.update_channel import UpdateChannelInput, UpdateChannelUseCase
from src.domain.entities.channel import Channel


class CreateChannelRequest(BaseModel):
    """HTTP payload used to create a workspace channel configuration.

    Purpose:
    - Capture provider routing fields while keeping payload schema explicit.

    Constraints:
    - Unknown fields are rejected.
    - `provider` must be non-empty.
    """

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)
    group: str | None = None
    is_active: bool = True


class UpdateChannelRequest(BaseModel):
    """HTTP payload used to fully update channel routing metadata.

    Architectural role:
    - Inbound DTO for compatibility channel management APIs.
    """

    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)
    group: str | None = None
    is_active: bool = True


class DisableChannelRequest(BaseModel):
    """HTTP payload used to scope channel-disable operation to workspace."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1)


class ChannelResponse(BaseModel):
    """Stable outbound API contract for channel resources."""

    model_config = ConfigDict(extra="forbid")

    id: str
    workspace_id: str
    provider: str
    config: dict[str, Any]
    group: str | None
    is_active: bool


class ChannelControllerFactory:
    """Compose channel-management HTTP routes using application use cases.

    Responsibilities:
    - Map inbound request contracts into use-case inputs.
    - Normalize known validation/lookup failures into HTTP status codes.
    - Keep channel policy decisions in application layer.
    """

    def __init__(
        self,
        create_channel_use_case: CreateChannelUseCase,
        list_channels_use_case: ListChannelsUseCase,
        update_channel_use_case: UpdateChannelUseCase,
        disable_channel_use_case: DisableChannelUseCase,
    ) -> None:
        """Store route dependencies for create/list/update/disable handlers."""

        self._create_channel_use_case = create_channel_use_case
        self._list_channels_use_case = list_channels_use_case
        self._update_channel_use_case = update_channel_use_case
        self._disable_channel_use_case = disable_channel_use_case

    def build(self) -> APIRouter:
        """Build router with workspace-scoped channel management endpoints.

        Returns:
            APIRouter: Router exposing channel CRUD-like compatibility actions.
        """

        router = APIRouter(tags=["channels"])

        @router.post(
            "/workspaces/{workspace_id}/channels",
            response_model=ChannelResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_channel(workspace_id: str, request: CreateChannelRequest) -> ChannelResponse:
            """Create a new channel for the provided workspace.

            Args:
                workspace_id: Workspace identifier from URL path.
                request: Validated channel-creation payload.

            Returns:
                ChannelResponse: Persisted channel representation.

            Edge cases:
            - Invalid input maps to HTTP 400.
            - Unknown workspace maps to HTTP 404.
            """

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
            """List channels configured for one workspace.

            Args:
                workspace_id: Workspace identifier from URL path.

            Returns:
                list[ChannelResponse]: Workspace channel DTO collection.
            """

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
            """Replace persisted channel metadata for the requested channel id.

            Args:
                channel_id: Target channel identifier.
                request: Payload containing workspace scope and replacement data.

            Returns:
                ChannelResponse: Updated channel representation.
            """

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
            """Disable a channel for the provided workspace scope.

            Args:
                channel_id: Target channel identifier.
                request: Payload carrying workspace ownership scope.

            Returns:
                ChannelResponse: Disabled (or already-disabled) channel state.
            """

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
    """Map channel domain entity into transport-safe API response model."""

    return ChannelResponse(
        id=channel.id,
        workspace_id=channel.workspace_id,
        provider=channel.provider,
        config=channel.config,
        group=channel.group,
        is_active=channel.is_active,
    )

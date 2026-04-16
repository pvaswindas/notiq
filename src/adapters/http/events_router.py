import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from src.adapters.http.dependencies.auth import AuthContext, require_auth
from src.modules.notifications.application.dto.send_notification_command import SendNotificationCommand
from src.modules.notifications.application.use_cases.send_notification_use_case import SendNotificationUseCase
from src.modules.notifications.ports.id_generator_port import IdGeneratorPort


class EventIngestionRequest(BaseModel):
    """Request contract for legacy event fan-out ingestion endpoint.

    Purpose:
    - Capture minimal event payload required by compatibility `/events` path.

    Constraints:
    - `event_type` must be non-empty.
    - `payload` remains schema-flexible for backward compatibility.
    """

    event_type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class EventIngestionResponse(BaseModel):
    """Response contract indicating asynchronous event acceptance.

    Purpose:
    - Return a stable response shape for clients using legacy ingestion.

    Constraints:
    - Response intentionally avoids delivery status semantics.
    """

    model_config = ConfigDict(extra="forbid")

    status: str = "accepted"


class EventRouterFactory:
    """Build HTTP routes for the legacy `/events` compatibility endpoint.

    Architectural role:
    - Inbound adapter that preserves the legacy `/events` contract while
      routing execution into the modular notification pipeline.
    """

    def __init__(
        self,
        send_notification_use_case: SendNotificationUseCase,
        id_generator: IdGeneratorPort,
    ) -> None:
        """Store modular dependencies used to serve legacy event ingestion.

        Args:
            send_notification_use_case: Primary notification intake use case.
            id_generator: Generates compatibility event identifiers.
        """

        self._send_notification_use_case = send_notification_use_case
        self._id_generator = id_generator
        self._logger = logging.getLogger(__name__)

    def build(self) -> APIRouter:
        """Create and return API router for legacy event ingestion.

        Returns:
            APIRouter: Router exposing `POST /events`.

        Important:
        - This adapter preserves the legacy request/response contract.
        - Business orchestration is delegated to `SendNotificationUseCase`.
        """

        router = APIRouter(tags=["events"])

        @router.post("/events", response_model=EventIngestionResponse)
        async def ingest_event(
            request: EventIngestionRequest,
            auth: AuthContext = Depends(require_auth),
        ) -> EventIngestionResponse:
            """Accept a legacy event and enqueue modular delivery jobs.

            Args:
                request: Validated HTTP request payload.

            Returns:
                EventIngestionResponse: Static acceptance response.

            Internal flow:
            - Resolve workspace from authenticated API key context.
            - Map legacy request into modular send-notification command.
            - Execute modular intake flow that persists `delivery_jobs`.
            - Normalize known validation failures to HTTP 400.

            Edge cases:
            - Unexpected runtime errors are mapped to HTTP 500.
            """

            command = SendNotificationCommand(
                workspace_id=auth.workspace_id,
                event_id=self._id_generator.new_id(),
                event_name=request.event_type,
                payload=request.payload,
            )
            try:
                self._logger.info(
                    "legacy /events endpoint routed to modular notification pipeline",
                    extra={
                        "workspace_id": auth.workspace_id,
                        "api_key_id": auth.api_key_id,
                        "event_type": request.event_type,
                    },
                )
                await self._send_notification_use_case.execute(command)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except Exception as exc:
                raise HTTPException(status_code=500, detail="failed to process event") from exc
            return EventIngestionResponse(status="accepted")

        return router

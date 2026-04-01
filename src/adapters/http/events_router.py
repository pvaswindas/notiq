from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from src.adapters.http.dependencies.auth import AuthContext, require_auth
from src.application.use_cases.process_event_use_case import ProcessEventUseCase
from src.domain.entities.event import Event


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
    - Inbound adapter that translates HTTP payloads into application use-case
      calls without containing routing or delivery business policies.
    """

    def __init__(self, process_event_use_case: ProcessEventUseCase) -> None:
        """Store process-event use case dependency for route handler calls.

        Args:
            process_event_use_case: Application use case that handles channel
                fan-out and event queue enqueueing.
        """

        self._process_event_use_case = process_event_use_case

    def build(self) -> APIRouter:
        """Create and return API router for legacy event ingestion.

        Returns:
            APIRouter: Router exposing `POST /events`.

        Important:
        - This adapter should only validate/translate protocol concerns.
        - Business orchestration must remain in `ProcessEventUseCase`.
        """

        router = APIRouter(tags=["events"])

        @router.post("/events", response_model=EventIngestionResponse)
        async def ingest_event(
            request: EventIngestionRequest,
            auth: AuthContext = Depends(require_auth),
        ) -> EventIngestionResponse:
            """Accept a legacy event and enqueue per-channel tasks.

            Args:
                request: Validated HTTP request payload.

            Returns:
                EventIngestionResponse: Static acceptance response.

            Internal flow:
            - Map request to legacy domain `Event`.
            - Execute compatibility use case fan-out behavior.
            - Normalize known validation failures to HTTP 400.

            Edge cases:
            - Unexpected runtime errors are mapped to HTTP 500.
            """

            event = Event(
                workspace_id=auth.workspace_id,
                event_type=request.event_type,
                payload=request.payload,
            )
            try:
                await self._process_event_use_case.execute(event)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except Exception as exc:
                raise HTTPException(status_code=500, detail="failed to process event") from exc
            return EventIngestionResponse(status="accepted")

        return router

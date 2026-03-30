from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from src.application.use_cases.process_event_use_case import ProcessEventUseCase
from src.domain.entities.event import Event


class EventIngestionRequest(BaseModel):
    workspace_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class EventIngestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "accepted"


class EventRouterFactory:
    def __init__(self, process_event_use_case: ProcessEventUseCase) -> None:
        self._process_event_use_case = process_event_use_case

    def build(self) -> APIRouter:
        router = APIRouter(tags=["events"])

        @router.post("/events", response_model=EventIngestionResponse)
        async def ingest_event(request: EventIngestionRequest) -> EventIngestionResponse:
            event = Event(
                workspace_id=request.workspace_id,
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

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from src.adapters.http.dependencies.auth import AuthContext, require_auth
from src.modules.notifications.application.use_cases.get_dead_letter_job_use_case import (
    GetDeadLetterJobCommand,
    GetDeadLetterJobUseCase,
)
from src.modules.notifications.application.use_cases.list_dead_letter_jobs_use_case import (
    ListDeadLetterJobsCommand,
    ListDeadLetterJobsUseCase,
)
from src.modules.notifications.application.use_cases.replay_dead_letter_job_use_case import (
    ReplayDeadLetterJobCommand,
    ReplayDeadLetterJobResult,
    ReplayDeadLetterJobUseCase,
)
from src.modules.notifications.domain.entities.dead_letter_job import DeadLetterJob


class DeadLetterJobResponse(BaseModel):
    """Transport-safe dead-letter job representation."""

    model_config = ConfigDict(extra="forbid")

    id: str
    original_job_id: str
    workspace_id: str
    channel_id: str
    provider: str
    payload: dict
    failure_reason: str
    failure_count: int
    last_attempt_at: str
    created_at: str


class ReplayDeadLetterJobResponse(BaseModel):
    """Replay outcome response."""

    model_config = ConfigDict(extra="forbid")

    delivery_job_id: str = Field(min_length=1)


class DeadLetterControllerFactory:
    """Compose authenticated DLQ routes."""

    def __init__(
        self,
        list_dead_letter_jobs_use_case: ListDeadLetterJobsUseCase,
        get_dead_letter_job_use_case: GetDeadLetterJobUseCase,
        replay_dead_letter_job_use_case: ReplayDeadLetterJobUseCase,
    ) -> None:
        self._list_dead_letter_jobs_use_case = list_dead_letter_jobs_use_case
        self._get_dead_letter_job_use_case = get_dead_letter_job_use_case
        self._replay_dead_letter_job_use_case = replay_dead_letter_job_use_case

    def build(self) -> APIRouter:
        router = APIRouter(tags=["dead-letters"])

        @router.get("/dead-letters", response_model=list[DeadLetterJobResponse])
        async def list_dead_letters(
            workspace_id: str = Query(min_length=1),
            limit: int = Query(default=100, ge=1, le=500),
            offset: int = Query(default=0, ge=0),
            auth: AuthContext = Depends(require_auth),
        ) -> list[DeadLetterJobResponse]:
            _enforce_workspace_access(auth, workspace_id)
            try:
                jobs = await self._list_dead_letter_jobs_use_case.execute(
                    ListDeadLetterJobsCommand(workspace_id=workspace_id, limit=limit, offset=offset)
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return [_to_response(job) for job in jobs]

        @router.get("/dead-letters/{dead_letter_job_id}", response_model=DeadLetterJobResponse)
        async def get_dead_letter(
            dead_letter_job_id: str,
            auth: AuthContext = Depends(require_auth),
        ) -> DeadLetterJobResponse:
            try:
                job = await self._get_dead_letter_job_use_case.execute(
                    GetDeadLetterJobCommand(dead_letter_job_id=dead_letter_job_id, workspace_id=auth.workspace_id)
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            return _to_response(job)

        @router.post("/dead-letters/{dead_letter_job_id}/replay", response_model=ReplayDeadLetterJobResponse)
        async def replay_dead_letter(
            dead_letter_job_id: str,
            auth: AuthContext = Depends(require_auth),
        ) -> ReplayDeadLetterJobResponse:
            try:
                result: ReplayDeadLetterJobResult = await self._replay_dead_letter_job_use_case.execute(
                    ReplayDeadLetterJobCommand(dead_letter_job_id=dead_letter_job_id, workspace_id=auth.workspace_id)
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except PermissionError as exc:
                raise HTTPException(status_code=403, detail=str(exc)) from exc
            return ReplayDeadLetterJobResponse(delivery_job_id=result.delivery_job_id)

        return router


def _enforce_workspace_access(auth: AuthContext, workspace_id: str) -> None:
    if auth.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="workspace access denied")


def _to_response(job: DeadLetterJob) -> DeadLetterJobResponse:
    return DeadLetterJobResponse(
        id=job.dead_letter_job_id,
        original_job_id=job.original_job_id,
        workspace_id=job.workspace_id,
        channel_id=job.channel_id,
        provider=job.provider,
        payload=dict(job.payload),
        failure_reason=job.failure_reason,
        failure_count=job.failure_count,
        last_attempt_at=job.last_attempt_at.isoformat(),
        created_at=job.created_at.isoformat(),
    )


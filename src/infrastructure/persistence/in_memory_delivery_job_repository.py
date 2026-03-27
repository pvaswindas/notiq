import asyncio
from datetime import datetime, timezone

from src.modules.notifications.domain.entities.delivery_job import DeliveryJob, DeliveryJobStatus
from src.modules.notifications.ports.delivery_job_repository_port import DeliveryJobRepositoryPort


class InMemoryDeliveryJobRepository(DeliveryJobRepositoryPort):
    """
    Purpose:
    - Provide async in-memory persistence for delivery jobs.

    Responsibilities:
    - Persist delivery jobs by id.
    - Support lifecycle updates.
    - Return pending jobs that are due for processing.

    Constraints:
    - Process-local storage only.
    - Not suitable for production durability or cross-process coordination.
    """

    def __init__(self) -> None:
        """
        Purpose:
        - Initialize in-memory storage structures for delivery jobs.

        Side effects:
        - Creates process-local dictionary and async lock.
        """

        self._jobs: dict[str, DeliveryJob] = {}
        self._lock = asyncio.Lock()

    async def save(self, job: DeliveryJob) -> None:
        """
        Purpose:
        - Persist a new delivery job entry in memory.

        Inputs:
        - job: DeliveryJob to store.

        Side effects:
        - Mutates internal job dictionary.
        """

        async with self._lock:
            if job.job_id in self._jobs:
                raise ValueError(f"delivery job already exists: {job.job_id}")
            self._jobs[job.job_id] = job

    async def update(self, job: DeliveryJob) -> None:
        """
        Purpose:
        - Update an existing in-memory delivery job state.

        Inputs:
        - job: DeliveryJob containing updated lifecycle fields.

        Side effects:
        - Replaces stored job snapshot by job_id.
        """

        async with self._lock:
            if job.job_id not in self._jobs:
                raise ValueError(f"delivery job not found: {job.job_id}")
            self._jobs[job.job_id] = job

    async def get_pending_jobs(self, limit: int) -> list[DeliveryJob]:
        """
        Purpose:
        - Return due jobs ready for worker execution.

        Inputs:
        - limit: Maximum number of jobs to return.

        Outputs:
        - list[DeliveryJob] filtered by PENDING status and retry schedule.
        """

        now = datetime.now(timezone.utc)
        async with self._lock:
            pending_jobs: list[DeliveryJob] = []
            for job in self._jobs.values():
                if job.status != DeliveryJobStatus.PENDING:
                    continue
                if job.next_retry_at is not None and job.next_retry_at > now:
                    continue
                pending_jobs.append(job)
                if len(pending_jobs) >= limit:
                    break
            return pending_jobs

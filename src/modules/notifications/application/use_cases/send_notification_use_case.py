from src.modules.notifications.application.dto.queued_delivery_dto import QueuedDeliveryResultDTO
from src.modules.notifications.application.dto.send_notification_command import SendNotificationCommand
from src.modules.notifications.application.mappers.event_message_mapper import EventMessageMapper
from src.modules.notifications.domain.entities.delivery_job import DeliveryJob
from src.modules.notifications.domain.entities.event import Event
from src.modules.notifications.domain.events.notification_enqueued import NotificationEnqueued
from src.modules.notifications.domain.events.notification_requested import NotificationRequested
from src.modules.notifications.domain.repositories import ChannelRepository, IdempotencyRepository
from src.modules.notifications.domain.services.idempotency_service import IdempotencyService
from src.modules.notifications.domain.services.rate_limit_service import RateLimitService
from src.modules.notifications.ports.delivery_job_repository_port import DeliveryJobRepositoryPort
from src.modules.notifications.ports.id_generator_port import IdGeneratorPort


class SendNotificationUseCase:
    """
    Purpose:
    - Orchestrate event submission into persistent delivery jobs.

    Responsibilities:
    - Validate submission preconditions.
    - Fetch active channels by workspace.
    - Enforce rate limiting.
    - Enforce race-safe idempotency.
    - Map messages and persist delivery jobs.

    Constraints:
    - Must not call provider adapters directly.
    """

    def __init__(
        self,
        channel_repository: ChannelRepository,
        idempotency_repository: IdempotencyRepository,
        delivery_job_repository: DeliveryJobRepositoryPort,
        message_mapper: EventMessageMapper,
        idempotency_service: IdempotencyService,
        rate_limit_service: RateLimitService,
        id_generator: IdGeneratorPort,
    ) -> None:
        """
        Purpose:
        - Initialize dependencies required for notification intake orchestration.

        Inputs:
        - channel_repository: Workspace channel retrieval contract.
        - idempotency_repository: Dedupe persistence contract.
        - delivery_job_repository: Delivery job persistence contract.
        - message_mapper: Event-to-message mapping component.
        - idempotency_service: Fingerprint generation service.
        - rate_limit_service: Workspace admission policy service.
        - id_generator: Job identifier generator.

        Side effects:
        - Stores references for use by execute().
        """

        self._channel_repository = channel_repository
        self._idempotency_repository = idempotency_repository
        self._delivery_job_repository = delivery_job_repository
        self._message_mapper = message_mapper
        self._idempotency_service = idempotency_service
        self._rate_limit_service = rate_limit_service
        self._id_generator = id_generator

    async def execute(self, command: SendNotificationCommand) -> QueuedDeliveryResultDTO:
        """
        Purpose:
        - Execute the notification intake workflow for a single inbound event command.

        Inputs:
        - command: Notification request command containing workspace and event payload.

        Outputs:
        - QueuedDeliveryResultDTO with counts of enqueued and duplicate-skipped jobs.

        Side effects:
        - Reads workspace channels.
        - Performs rate-limit and idempotency checks.
        - Persists delivery jobs for asynchronous worker processing.
        """

        if not command.workspace_id or not command.event_id or not command.event_name:
            raise ValueError("workspace_id, event_id, and event_name are required")

        NotificationRequested(workspace_id=command.workspace_id, event_id=command.event_id)

        # Rate limit is evaluated before persistence work to protect downstream capacity.
        if not self._rate_limit_service.allow_workspace(command.workspace_id):
            return QueuedDeliveryResultDTO(enqueued_jobs=0, skipped_duplicates=0)

        event = Event(
            event_id=command.event_id,
            workspace_id=command.workspace_id,
            event_name=command.event_name,
            payload=command.payload,
        )

        # Workspace-scoped channel routing.
        active_channels = await self._channel_repository.list_active_by_workspace(command.workspace_id)
        event_fingerprint = self._idempotency_service.create_event_fingerprint(event)

        enqueued_jobs = 0
        skipped_duplicates = 0

        for channel in active_channels:
            channel_fingerprint = self._idempotency_service.create_channel_fingerprint(
                event_fingerprint=event_fingerprint,
                channel_id=channel.channel_id,
            )

            # Atomic claim prevents races between concurrent submissions.
            claimed = await self._idempotency_repository.claim(channel_fingerprint.value)
            if not claimed:
                skipped_duplicates += 1
                continue

            message = self._message_mapper.to_message(event=event, channel=channel)
            job = DeliveryJob(
                job_id=self._id_generator.new_id(),
                workspace_id=event.workspace_id,
                channel_id=channel.channel_id,
                provider_key=channel.provider_key,
                destination=channel.address,
                message=message,
                dedupe_key=channel_fingerprint.value,
            )

            await self._delivery_job_repository.save(job)
            NotificationEnqueued(workspace_id=event.workspace_id, job_id=job.job_id, channel_id=channel.channel_id)
            enqueued_jobs += 1

        return QueuedDeliveryResultDTO(enqueued_jobs=enqueued_jobs, skipped_duplicates=skipped_duplicates)

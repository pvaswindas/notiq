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
from src.modules.notifications.ports.event_queue_port import EventQueuePort
from src.modules.notifications.ports.id_generator_port import IdGeneratorPort


class SendNotificationUseCase:
    """
    Purpose:
    - Orchestrate event submission into queued delivery jobs.

    Responsibilities:
    - Validate submission preconditions.
    - Fetch active channels.
    - Deduplicate event-channel combinations.
    - Map messages and enqueue delivery jobs.

    Inputs:
    - channel_repository: ChannelRepository
    - idempotency_repository: IdempotencyRepository
    - event_queue: EventQueuePort
    - message_mapper: EventMessageMapper
    - idempotency_service: IdempotencyService
    - rate_limit_service: RateLimitService
    - id_generator: IdGeneratorPort

    Outputs:
    - QueuedDeliveryResultDTO from execute.

    Constraints:
    - Must not call provider adapters directly.
    """

    def __init__(
        self,
        channel_repository: ChannelRepository,
        idempotency_repository: IdempotencyRepository,
        event_queue: EventQueuePort,
        message_mapper: EventMessageMapper,
        idempotency_service: IdempotencyService,
        rate_limit_service: RateLimitService,
        id_generator: IdGeneratorPort,
    ) -> None:
        """
        Purpose:
        - Construct send-notification orchestration dependencies.

        Responsibilities:
        - Store repositories, ports, and domain services used by execute.

        Inputs:
        - channel_repository: ChannelRepository
        - idempotency_repository: IdempotencyRepository
        - event_queue: EventQueuePort
        - message_mapper: EventMessageMapper
        - idempotency_service: IdempotencyService
        - rate_limit_service: RateLimitService
        - id_generator: IdGeneratorPort

        Outputs:
        - None

        Constraints:
        - Dependencies must remain framework-independent.
        """

        self._channel_repository = channel_repository
        self._idempotency_repository = idempotency_repository
        self._event_queue = event_queue
        self._message_mapper = message_mapper
        self._idempotency_service = idempotency_service
        self._rate_limit_service = rate_limit_service
        self._id_generator = id_generator

    async def execute(self, command: SendNotificationCommand) -> QueuedDeliveryResultDTO:
        """
        Purpose:
        - Convert an inbound notification command into queued delivery jobs.

        Responsibilities:
        - Validate essential command input.
        - Build domain event context.
        - Apply rate-limit and idempotency checks.
        - Enqueue jobs for all active channels.

        Inputs:
        - command: SendNotificationCommand

        Outputs:
        - QueuedDeliveryResultDTO

        Constraints:
        - Event payload must remain dict-based and generic.
        """

        if not command.workspace_id or not command.event_id or not command.event_name:
            raise ValueError("workspace_id, event_id, and event_name are required")

        NotificationRequested(workspace_id=command.workspace_id, event_id=command.event_id)

        if not self._rate_limit_service.allow_workspace(command.workspace_id):
            return QueuedDeliveryResultDTO(enqueued_jobs=0, skipped_duplicates=0)

        event = Event(
            event_id=command.event_id,
            workspace_id=command.workspace_id,
            event_name=command.event_name,
            payload=command.payload,
        )

        active_channels = await self._channel_repository.list_active_by_workspace(command.workspace_id)
        event_fingerprint = self._idempotency_service.create_event_fingerprint(event)

        enqueued_jobs = 0
        skipped_duplicates = 0
        for channel in active_channels:
            channel_fingerprint = self._idempotency_service.create_channel_fingerprint(
                event_fingerprint=event_fingerprint,
                channel_id=channel.channel_id,
            )

            if await self._idempotency_repository.exists(channel_fingerprint.value):
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

            await self._event_queue.enqueue(job)
            await self._idempotency_repository.save(channel_fingerprint.value)
            NotificationEnqueued(workspace_id=event.workspace_id, job_id=job.job_id, channel_id=channel.channel_id)
            enqueued_jobs += 1

        return QueuedDeliveryResultDTO(enqueued_jobs=enqueued_jobs, skipped_duplicates=skipped_duplicates)

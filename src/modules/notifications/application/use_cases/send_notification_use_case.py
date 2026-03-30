from src.modules.notifications.application.dto.queued_delivery_dto import QueuedDeliveryResultDTO
from src.modules.notifications.application.dto.send_notification_command import SendNotificationCommand
from src.modules.notifications.application.mappers.event_message_mapper import EventMessageMapper
from src.modules.notifications.application.services.provider_account_resolver import ProviderAccountResolver
from src.modules.notifications.domain.entities.delivery_job import DeliveryJob
from src.modules.notifications.domain.entities.event import Event
from src.modules.notifications.ports.channel_repository_port import ChannelRepositoryPort
from src.modules.notifications.ports.delivery_job_repository_port import DeliveryJobRepositoryPort
from src.modules.notifications.ports.id_generator_port import IdGeneratorPort
from src.modules.notifications.ports.idempotency_repository_port import IdempotencyRepositoryPort
from src.modules.notifications.ports.workspace_repository_port import WorkspaceRepositoryPort
from src.modules.notifications.domain.services.idempotency_service import IdempotencyService


class SendNotificationUseCase:
    """Orchestrate inbound event intake into persisted delivery jobs."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepositoryPort,
        channel_repository: ChannelRepositoryPort,
        idempotency_repository: IdempotencyRepositoryPort,
        delivery_job_repository: DeliveryJobRepositoryPort,
        provider_account_resolver: ProviderAccountResolver,
        message_mapper: EventMessageMapper,
        idempotency_service: IdempotencyService,
        id_generator: IdGeneratorPort,
    ) -> None:
        """Initialize all ports/services required for notification intake flow."""

        self._workspace_repository = workspace_repository
        self._channel_repository = channel_repository
        self._idempotency_repository = idempotency_repository
        self._delivery_job_repository = delivery_job_repository
        self._provider_account_resolver = provider_account_resolver
        self._message_mapper = message_mapper
        self._idempotency_service = idempotency_service
        self._id_generator = id_generator

    async def execute(self, command: SendNotificationCommand) -> QueuedDeliveryResultDTO:
        """Validate input, resolve channels/accounts, dedupe, and enqueue jobs.

        Important constraints:
        - Workspace must exist and be active.
        - Idempotency is enforced per `(event, channel)` fingerprint.
        - When `channel_ids` are provided, routing is restricted to that subset.
        """

        if not command.workspace_id or not command.event_id or not command.event_name:
            raise ValueError("workspace_id, event_id, and event_name are required")

        workspace = await self._workspace_repository.get_by_id(command.workspace_id)
        if workspace is None:
            raise ValueError(f"workspace not found: {command.workspace_id}")
        if not workspace.is_active:
            raise ValueError(f"workspace is inactive: {command.workspace_id}")

        event = Event(
            event_id=command.event_id,
            workspace_id=command.workspace_id,
            event_name=command.event_name,
            payload=command.payload,
        )

        active_channels = await self._channel_repository.list_active_by_workspace(command.workspace_id)
        if command.channel_ids:
            channel_id_set = set(command.channel_ids)
            active_channels = [channel for channel in active_channels if channel.channel_id in channel_id_set]

        event_fingerprint = self._idempotency_service.create_event_fingerprint(event)
        enqueued_jobs = 0
        skipped_duplicates = 0

        for channel in active_channels:
            provider_account = await self._provider_account_resolver.resolve_for_channel(channel)
            channel_fingerprint = self._idempotency_service.create_channel_fingerprint(
                event_fingerprint=event_fingerprint,
                channel_id=channel.channel_id,
            )

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
                provider_account_id=provider_account.provider_account_id,
                destination=channel.destination,
                message=message,
                dedupe_key=channel_fingerprint.value,
            )

            await self._delivery_job_repository.save(job)
            enqueued_jobs += 1

        return QueuedDeliveryResultDTO(enqueued_jobs=enqueued_jobs, skipped_duplicates=skipped_duplicates)

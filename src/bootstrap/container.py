from dataclasses import dataclass

from src.bootstrap.workers.notification_worker import NotificationWorker
from src.infrastructure.id_generator.uuid_id_generator import UUIDIdGenerator
from src.infrastructure.persistence.in_memory_channel_repository import InMemoryChannelRepository
from src.infrastructure.persistence.in_memory_delivery_job_repository import InMemoryDeliveryJobRepository
from src.infrastructure.persistence.in_memory_idempotency_repository import InMemoryIdempotencyRepository
from src.modules.notifications.adapters.outbound.telegram.telegram_notifier import TelegramNotifier
from src.modules.notifications.application.mappers.event_message_mapper import EventMessageMapper
from src.modules.notifications.application.services.sender_registry import SenderRegistry
from src.modules.notifications.application.use_cases.process_delivery_job_use_case import ProcessDeliveryJobUseCase
from src.modules.notifications.application.use_cases.send_notification_use_case import SendNotificationUseCase
from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.services.idempotency_service import IdempotencyService
from src.modules.notifications.domain.services.rate_limit_service import RateLimitService


@dataclass(slots=True)
class Container:
    """
    Purpose:
    - Hold fully wired application dependencies.

    Responsibilities:
    - Expose use cases and worker instances for runtime composition.

    Inputs:
    - send_notification_use_case: SendNotificationUseCase
    - process_delivery_job_use_case: ProcessDeliveryJobUseCase
    - notification_worker: NotificationWorker

    Outputs:
    - Container instance.

    Constraints:
    - Dependencies must be injected and composed centrally.
    """

    send_notification_use_case: SendNotificationUseCase
    process_delivery_job_use_case: ProcessDeliveryJobUseCase
    notification_worker: NotificationWorker


class ContainerFactory:
    """
    Purpose:
    - Build dependency injection container for Notiq runtime.

    Responsibilities:
    - Bind ports to infrastructure implementations.
    - Compose application services, use cases, and worker.

    Inputs:
    - None.

    Outputs:
    - Container

    Constraints:
    - Acts as the single composition root.
    """

    def build(self) -> Container:
        """
        Purpose:
        - Construct runtime dependency graph.

        Responsibilities:
        - Instantiate infrastructure adapters.
        - Compose application-level services.
        - Inject dependencies into use cases and worker.

        Inputs:
        - None.

        Outputs:
        - Container

        Constraints:
        - Uses in-memory infrastructure implementations for current runtime.
        """

        seed_channels = [
            Channel(
                channel_id="channel-1",
                workspace_id="workspace-1",
                name="ops-telegram",
                provider_key="telegram",
                address="123456789",
                metadata={"bot_token": "placeholder"},
            )
        ]

        channel_repository = InMemoryChannelRepository(channels=seed_channels)
        idempotency_repository = InMemoryIdempotencyRepository()
        delivery_job_repository = InMemoryDeliveryJobRepository()
        id_generator = UUIDIdGenerator()

        telegram_sender = TelegramNotifier()
        sender_registry = SenderRegistry(senders={"telegram": telegram_sender})
        message_mapper = EventMessageMapper()
        idempotency_service = IdempotencyService()
        rate_limit_service = RateLimitService(max_events_per_minute=120)

        send_notification_use_case = SendNotificationUseCase(
            channel_repository=channel_repository,
            idempotency_repository=idempotency_repository,
            delivery_job_repository=delivery_job_repository,
            message_mapper=message_mapper,
            idempotency_service=idempotency_service,
            rate_limit_service=rate_limit_service,
            id_generator=id_generator,
        )

        process_delivery_job_use_case = ProcessDeliveryJobUseCase(
            sender_registry=sender_registry,
            delivery_job_repository=delivery_job_repository,
        )
        notification_worker = NotificationWorker(
            delivery_job_repository=delivery_job_repository,
            process_delivery_job_use_case=process_delivery_job_use_case,
            batch_size=50,
            poll_interval_seconds=1.0,
        )

        return Container(
            send_notification_use_case=send_notification_use_case,
            process_delivery_job_use_case=process_delivery_job_use_case,
            notification_worker=notification_worker,
        )

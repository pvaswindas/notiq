from dataclasses import dataclass

from src.bootstrap.settings import settings
from src.bootstrap.workers.notification_worker import NotificationWorker
from src.infrastructure.id_generator.uuid_id_generator import UUIDIdGenerator
from src.infrastructure.persistence.postgres.channel_repository import PostgresChannelRepository
from src.infrastructure.persistence.postgres.delivery_job_repository import PostgresDeliveryJobRepository
from src.infrastructure.persistence.postgres.idempotency_repository import PostgresIdempotencyRepository
from src.infrastructure.persistence.postgres.provider_account_repository import PostgresProviderAccountRepository
from src.infrastructure.persistence.postgres.workspace_repository import PostgresWorkspaceRepository
from src.modules.notifications.adapters.outbound.email.email_notifier import EmailNotifier
from src.modules.notifications.adapters.outbound.telegram.telegram_notifier import TelegramNotifier
from src.modules.notifications.application.mappers.event_message_mapper import EventMessageMapper
from src.modules.notifications.application.services.provider_account_resolver import ProviderAccountResolver
from src.modules.notifications.application.services.sender_registry import SenderRegistry
from src.modules.notifications.application.use_cases.process_delivery_job_use_case import ProcessDeliveryJobUseCase
from src.modules.notifications.application.use_cases.send_notification_use_case import SendNotificationUseCase
from src.modules.notifications.domain.services.idempotency_service import IdempotencyService


@dataclass(slots=True)
class Container:
    """Aggregate root for runtime dependencies used by API and worker entrypoints."""

    send_notification_use_case: SendNotificationUseCase
    process_delivery_job_use_case: ProcessDeliveryJobUseCase
    notification_worker: NotificationWorker


class ContainerFactory:
    """Compose concrete adapters and use cases for the running process."""

    def build(self) -> Container:
        """Build and return a fully wired container.

        This is the composition root for the notifications module. It binds
        infrastructure adapters to application ports and returns ready-to-use
        use cases plus worker orchestration components.
        """

        workspace_repository = PostgresWorkspaceRepository()
        channel_repository = PostgresChannelRepository()
        provider_account_repository = PostgresProviderAccountRepository()
        idempotency_repository = PostgresIdempotencyRepository()
        delivery_job_repository = PostgresDeliveryJobRepository()
        id_generator = UUIDIdGenerator()

        sender_registry = SenderRegistry(
            senders={
                "telegram": TelegramNotifier(),
                "email": EmailNotifier(),
            }
        )
        provider_account_resolver = ProviderAccountResolver(provider_account_repository=provider_account_repository)
        message_mapper = EventMessageMapper()
        idempotency_service = IdempotencyService()

        send_notification_use_case = SendNotificationUseCase(
            workspace_repository=workspace_repository,
            channel_repository=channel_repository,
            idempotency_repository=idempotency_repository,
            delivery_job_repository=delivery_job_repository,
            provider_account_resolver=provider_account_resolver,
            message_mapper=message_mapper,
            idempotency_service=idempotency_service,
            id_generator=id_generator,
        )

        process_delivery_job_use_case = ProcessDeliveryJobUseCase(
            sender_registry=sender_registry,
            provider_account_repository=provider_account_repository,
            delivery_job_repository=delivery_job_repository,
        )

        notification_worker = NotificationWorker(
            worker_id=settings.worker_id,
            delivery_job_repository=delivery_job_repository,
            process_delivery_job_use_case=process_delivery_job_use_case,
            batch_size=settings.worker_batch_size,
            poll_interval_seconds=settings.worker_poll_interval_seconds,
            lease_seconds=settings.worker_lease_seconds,
        )

        return Container(
            send_notification_use_case=send_notification_use_case,
            process_delivery_job_use_case=process_delivery_job_use_case,
            notification_worker=notification_worker,
        )

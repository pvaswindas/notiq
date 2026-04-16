from dataclasses import dataclass

from src.application.use_cases.create_channel import CreateChannelUseCase
from src.application.use_cases.create_workspace import CreateWorkspaceUseCase
from src.application.use_cases.disable_channel import DisableChannelUseCase
from src.application.use_cases.disable_workspace import DisableWorkspaceUseCase
from src.application.use_cases.get_workspace import GetWorkspaceUseCase
from src.application.use_cases.list_channels import ListChannelsUseCase
from src.application.use_cases.list_workspaces import ListWorkspacesUseCase
from src.application.use_cases.update_channel import UpdateChannelUseCase
from src.bootstrap.settings import settings
from src.bootstrap.workers.notification_worker import NotificationWorker
from src.application.services.audit_logger import AuditLogger
from src.infrastructure.database.repositories.postgres_audit_log_repository import PostgresAuditLogRepository
from src.infrastructure.database.repositories.postgres_channel_repository import (
    PostgresChannelRepository as PublicApiPostgresChannelRepository,
)
from src.infrastructure.database.repositories.postgres_workspace_repository import (
    PostgresWorkspaceRepository as PublicApiPostgresWorkspaceRepository,
)
from src.infrastructure.id_generator.uuid_id_generator import UUIDIdGenerator
from src.infrastructure.persistence.postgres.channel_repository import (
    PostgresChannelRepository as NotificationsPostgresChannelRepository,
)
from src.infrastructure.persistence.postgres.delivery_job_repository import PostgresDeliveryJobRepository
from src.infrastructure.persistence.postgres.idempotency_repository import PostgresIdempotencyRepository
from src.infrastructure.persistence.postgres.provider_account_repository import PostgresProviderAccountRepository
from src.infrastructure.persistence.postgres.workspace_repository import (
    PostgresWorkspaceRepository as NotificationsPostgresWorkspaceRepository,
)
from src.infrastructure.database.repositories.postgres_rate_limit_config_repository import PostgresRateLimitConfigRepository
from src.infrastructure.redis.redis_delivery_rate_limiter import RedisDeliveryRateLimiter
from src.modules.notifications.adapters.outbound.email.email_notifier import EmailNotifier
from src.modules.notifications.adapters.outbound.telegram.telegram_notifier import TelegramNotifier
from src.modules.notifications.application.mappers.event_message_mapper import EventMessageMapper
from src.modules.notifications.application.services.delivery_safety_service import DeliverySafetyService
from src.modules.notifications.application.services.provider_account_resolver import ProviderAccountResolver
from src.modules.notifications.application.services.sender_registry import SenderRegistry
from src.modules.notifications.application.use_cases.process_delivery_job_use_case import ProcessDeliveryJobUseCase
from src.modules.notifications.application.use_cases.send_notification_use_case import SendNotificationUseCase
from src.modules.notifications.ports.id_generator_port import IdGeneratorPort
from src.modules.notifications.domain.services.idempotency_service import IdempotencyService


@dataclass(slots=True)
class Container:
    """Aggregate root for runtime dependencies used by API and worker entrypoints."""

    id_generator: IdGeneratorPort
    send_notification_use_case: SendNotificationUseCase
    process_delivery_job_use_case: ProcessDeliveryJobUseCase
    create_workspace_use_case: CreateWorkspaceUseCase
    disable_workspace_use_case: DisableWorkspaceUseCase
    get_workspace_use_case: GetWorkspaceUseCase
    list_workspaces_use_case: ListWorkspacesUseCase
    create_channel_use_case: CreateChannelUseCase
    list_channels_use_case: ListChannelsUseCase
    update_channel_use_case: UpdateChannelUseCase
    disable_channel_use_case: DisableChannelUseCase
    notification_worker: NotificationWorker


class ContainerFactory:
    """Compose concrete adapters and use cases for the running process."""

    def build(self) -> Container:
        """Build and return a fully wired container.

        This is the composition root for the notifications module. It binds
        infrastructure adapters to application ports and returns ready-to-use
        use cases plus worker orchestration components.
        """

        notification_workspace_repository = NotificationsPostgresWorkspaceRepository()
        notification_channel_repository = NotificationsPostgresChannelRepository()
        provider_account_repository = PostgresProviderAccountRepository()
        idempotency_repository = PostgresIdempotencyRepository()
        delivery_job_repository = PostgresDeliveryJobRepository()
        rate_limit_config_repository = PostgresRateLimitConfigRepository()
        delivery_rate_limiter = RedisDeliveryRateLimiter()
        id_generator = UUIDIdGenerator()

        public_api_workspace_repository = PublicApiPostgresWorkspaceRepository()
        public_api_channel_repository = PublicApiPostgresChannelRepository()
        audit_log_repository = PostgresAuditLogRepository()
        audit_logger = AuditLogger(audit_log_repository=audit_log_repository)

        sender_registry = SenderRegistry(
            senders={
                "telegram": TelegramNotifier(),
                "email": EmailNotifier(),
            }
        )
        provider_account_resolver = ProviderAccountResolver(provider_account_repository=provider_account_repository)
        message_mapper = EventMessageMapper()
        idempotency_service = IdempotencyService()
        delivery_safety_service = DeliverySafetyService(
            rate_limiter=delivery_rate_limiter,
            settings=settings,
            rate_limit_config_repository=rate_limit_config_repository,
        )

        send_notification_use_case = SendNotificationUseCase(
            workspace_repository=notification_workspace_repository,
            channel_repository=notification_channel_repository,
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
            delivery_safety_service=delivery_safety_service,
            settings=settings,
        )
        notification_worker = NotificationWorker(
            worker_id=settings.worker_id,
            delivery_job_repository=delivery_job_repository,
            process_delivery_job_use_case=process_delivery_job_use_case,
            batch_size=settings.worker_batch_size,
            poll_interval_seconds=settings.worker_poll_interval_seconds,
            lease_seconds=settings.worker_lease_seconds,
        )

        create_workspace_use_case = CreateWorkspaceUseCase(
            workspace_repository=public_api_workspace_repository,
            audit_logger=audit_logger,
        )
        disable_workspace_use_case = DisableWorkspaceUseCase(
            workspace_repository=public_api_workspace_repository,
            audit_logger=audit_logger,
        )
        get_workspace_use_case = GetWorkspaceUseCase(workspace_repository=public_api_workspace_repository)
        list_workspaces_use_case = ListWorkspacesUseCase(workspace_repository=public_api_workspace_repository)
        create_channel_use_case = CreateChannelUseCase(
            channel_repository=public_api_channel_repository,
            workspace_repository=public_api_workspace_repository,
            audit_logger=audit_logger,
        )
        list_channels_use_case = ListChannelsUseCase(
            channel_repository=public_api_channel_repository,
            workspace_repository=public_api_workspace_repository,
        )
        update_channel_use_case = UpdateChannelUseCase(
            channel_repository=public_api_channel_repository,
            audit_logger=audit_logger,
        )
        disable_channel_use_case = DisableChannelUseCase(
            channel_repository=public_api_channel_repository,
            audit_logger=audit_logger,
        )

        return Container(
            id_generator=id_generator,
            send_notification_use_case=send_notification_use_case,
            process_delivery_job_use_case=process_delivery_job_use_case,
            create_workspace_use_case=create_workspace_use_case,
            disable_workspace_use_case=disable_workspace_use_case,
            get_workspace_use_case=get_workspace_use_case,
            list_workspaces_use_case=list_workspaces_use_case,
            create_channel_use_case=create_channel_use_case,
            list_channels_use_case=list_channels_use_case,
            update_channel_use_case=update_channel_use_case,
            disable_channel_use_case=disable_channel_use_case,
            notification_worker=notification_worker,
        )

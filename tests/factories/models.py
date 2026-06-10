from datetime import datetime, timezone
import factory
from uuid import uuid4

from src.modules.notifications.domain.entities.workspace import Workspace
from src.modules.notifications.domain.entities.channel import Channel
from src.modules.notifications.domain.entities.provider_account import ProviderAccount
from src.modules.notifications.domain.entities.delivery_job import DeliveryJob, DeliveryJobStatus
from src.modules.notifications.domain.entities.event import Event


class WorkspaceFactory(factory.Factory):
    class Meta:
        model = Workspace

    workspace_id = factory.LazyFunction(lambda: f"ws_{uuid4().hex[:24]}")
    name = factory.Sequence(lambda n: f"Test Workspace {n}")
    is_active = True
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class ProviderAccountFactory(factory.Factory):
    class Meta:
        model = ProviderAccount

    provider_account_id = factory.LazyFunction(lambda: f"pa_{uuid4().hex[:24]}")
    workspace_id = factory.LazyFunction(lambda: f"ws_{uuid4().hex[:24]}")
    provider_key = "telegram"
    credentials = {"bot_token": "test_token"}
    is_active = True
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class ChannelFactory(factory.Factory):
    class Meta:
        model = Channel

    channel_id = factory.LazyFunction(lambda: f"ch_{uuid4().hex[:24]}")
    workspace_id = factory.SubFactory(WorkspaceFactory)
    provider_key = "telegram"
    destination = '{"chat_id": "123456"}'
    provider_account_id = factory.SubFactory(ProviderAccountFactory)


class EventFactory(factory.Factory):
    class Meta:
        model = Event

    event_id = factory.LazyFunction(lambda: f"ev_{uuid4().hex[:24]}")
    workspace_id = factory.SubFactory(WorkspaceFactory)
    event_name = "user.signed_up"
    payload = {"user_id": "usr_123", "email": "test@example.com"}


class DeliveryJobFactory(factory.Factory):
    class Meta:
        model = DeliveryJob

    job_id = factory.LazyFunction(lambda: f"job_{uuid4().hex[:24]}")
    workspace_id = factory.LazyFunction(lambda: f"ws_{uuid4().hex[:24]}")
    channel_id = factory.LazyFunction(lambda: f"ch_{uuid4().hex[:24]}")
    provider_key = "telegram"
    provider_account_id = factory.LazyFunction(lambda: f"pa_{uuid4().hex[:24]}")
    destination = '{"chat_id": "123456"}'
    message = '{"text": "Hello world"}'
    event_payload = {"user_id": "usr_123"}
    dedupe_key = factory.LazyFunction(lambda: f"dedupe_{uuid4().hex}")
    status = DeliveryJobStatus.PENDING
    retry_count = 0
    max_retries = 3
    processing_owner = None
    processing_expires_at = None
    last_error = None
    next_retry_at = None
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

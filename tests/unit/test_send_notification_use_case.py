import pytest
from unittest.mock import AsyncMock, MagicMock
from src.modules.notifications.application.dto.send_notification_command import SendNotificationCommand
from src.modules.notifications.application.use_cases.send_notification_use_case import SendNotificationUseCase
from src.modules.notifications.application.mappers.event_message_mapper import EventMessageMapper
from src.modules.notifications.domain.services.idempotency_service import IdempotencyService
from src.modules.notifications.domain.value_objects.event_fingerprint import EventFingerprint
from tests.factories.models import WorkspaceFactory, ChannelFactory, ProviderAccountFactory

@pytest.fixture
def use_case(mocker):
    return SendNotificationUseCase(
        workspace_repository=AsyncMock(),
        channel_repository=AsyncMock(),
        idempotency_repository=AsyncMock(),
        delivery_job_repository=AsyncMock(),
        provider_account_resolver=AsyncMock(),
        message_mapper=EventMessageMapper(),
        idempotency_service=IdempotencyService(),
        id_generator=mocker.Mock(new_id=mocker.Mock(return_value="test_id")),
        metrics_service=mocker.Mock(),
    )

@pytest.mark.asyncio
async def test_send_notification_happy_path(use_case):
    workspace = WorkspaceFactory()
    channel = ChannelFactory(workspace_id=workspace.workspace_id)
    provider_account = ProviderAccountFactory(workspace_id=workspace.workspace_id)
    
    use_case._workspace_repository.get_by_id.return_value = workspace
    use_case._channel_repository.list_active_by_workspace.return_value = [channel]
    use_case._idempotency_repository.claim.return_value = True
    use_case._provider_account_resolver.resolve_for_channel.return_value = provider_account
    
    command = SendNotificationCommand(
        workspace_id=workspace.workspace_id,
        event_id="evt_123",
        event_name="test_event",
        payload={"message": "Hello world"}
    )
    
    result = await use_case.execute(command)
    
    assert result.enqueued_jobs == 1
    assert result.skipped_duplicates == 0
    use_case._delivery_job_repository.save.assert_called_once()
    saved_job = use_case._delivery_job_repository.save.call_args[0][0]
    assert saved_job.workspace_id == workspace.workspace_id
    assert saved_job.channel_id == channel.channel_id
    assert saved_job.provider_account_id == provider_account.provider_account_id

@pytest.mark.asyncio
async def test_send_notification_inactive_workspace(use_case):
    workspace = WorkspaceFactory(is_active=False)
    use_case._workspace_repository.get_by_id.return_value = workspace
    
    command = SendNotificationCommand(
        workspace_id=workspace.workspace_id,
        event_id="evt_123",
        event_name="test_event",
        payload={}
    )
    
    with pytest.raises(ValueError, match="workspace is inactive"):
        await use_case.execute(command)
        
@pytest.mark.asyncio
async def test_send_notification_idempotency_skip(use_case):
    workspace = WorkspaceFactory()
    channel = ChannelFactory(workspace_id=workspace.workspace_id)
    provider_account = ProviderAccountFactory(workspace_id=workspace.workspace_id)
    
    use_case._workspace_repository.get_by_id.return_value = workspace
    use_case._channel_repository.list_active_by_workspace.return_value = [channel]
    use_case._idempotency_repository.claim.return_value = False
    use_case._provider_account_resolver.resolve_for_channel.return_value = provider_account
    
    command = SendNotificationCommand(
        workspace_id=workspace.workspace_id,
        event_id="evt_123",
        event_name="test_event",
        payload={}
    )
    
    result = await use_case.execute(command)
    assert result.enqueued_jobs == 0
    assert result.skipped_duplicates == 1
    use_case._delivery_job_repository.save.assert_not_called()

@pytest.mark.asyncio
async def test_send_notification_workspace_not_found(use_case):
    use_case._workspace_repository.get_by_id.return_value = None
    
    command = SendNotificationCommand(
        workspace_id="ws_not_found",
        event_id="evt_123",
        event_name="test_event",
        payload={}
    )
    
    with pytest.raises(ValueError, match="workspace not found"):
        await use_case.execute(command)

@pytest.mark.asyncio
async def test_send_notification_channel_ids_filtering(use_case):
    workspace = WorkspaceFactory()
    channel1 = ChannelFactory(workspace_id=workspace.workspace_id, channel_id="ch_1")
    channel2 = ChannelFactory(workspace_id=workspace.workspace_id, channel_id="ch_2")
    provider_account = ProviderAccountFactory(workspace_id=workspace.workspace_id)
    
    use_case._workspace_repository.get_by_id.return_value = workspace
    use_case._channel_repository.list_active_by_workspace.return_value = [channel1, channel2]
    use_case._idempotency_repository.claim.return_value = True
    use_case._provider_account_resolver.resolve_for_channel.return_value = provider_account
    
    command = SendNotificationCommand(
        workspace_id=workspace.workspace_id,
        event_id="evt_123",
        event_name="test_event",
        payload={"message": "Hello world"},
        channel_ids=["ch_1"]
    )
    
    result = await use_case.execute(command)
    assert result.enqueued_jobs == 1
    use_case._delivery_job_repository.save.assert_called_once()
    saved_job = use_case._delivery_job_repository.save.call_args[0][0]
    assert saved_job.channel_id == "ch_1"

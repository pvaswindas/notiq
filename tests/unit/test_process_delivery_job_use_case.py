import pytest
import httpx
from unittest.mock import AsyncMock, patch
from src.modules.notifications.application.use_cases.process_delivery_job_use_case import ProcessDeliveryJobUseCase
from src.modules.notifications.application.services.delivery_safety_service import DeliveryRateLimitResult
from src.modules.notifications.domain.entities.delivery_job import DeliveryJobStatus
from tests.factories.models import DeliveryJobFactory, ProviderAccountFactory

@pytest.fixture
def use_case(mocker):
    return ProcessDeliveryJobUseCase(
        sender_registry=mocker.Mock(),
        provider_account_repository=AsyncMock(),
        delivery_job_repository=AsyncMock(),
        dead_letter_job_repository=AsyncMock(),
        delivery_safety_service=AsyncMock(),
        settings=mocker.Mock(delivery_rate_limit_backoff_seconds=60),
        id_generator=mocker.Mock(new_id=mocker.Mock(return_value="test_id")),
        metrics_service=mocker.Mock(),
    )

@pytest.mark.asyncio
async def test_process_delivery_job_success(use_case, mocker):
    job = DeliveryJobFactory()
    provider_account = ProviderAccountFactory(
        workspace_id=job.workspace_id, 
        provider_account_id=job.provider_account_id,
        provider_key=job.provider_key
    )
    
    use_case._provider_account_repository.get_by_id.return_value = provider_account
    use_case._delivery_safety_service.check_rate_limit.return_value = DeliveryRateLimitResult(allowed=True)
    
    mock_sender = AsyncMock()
    use_case._sender_registry.resolve.return_value = mock_sender
    
    await use_case.execute(job)
    
    mock_sender.send.assert_called_once()
    use_case._delivery_job_repository.update.assert_called_once()
    
    updated_job = use_case._delivery_job_repository.update.call_args[0][0]
    assert updated_job.status == DeliveryJobStatus.SUCCESS
    assert updated_job.last_error is None

@pytest.mark.asyncio
async def test_process_delivery_job_rate_limited(use_case):
    job = DeliveryJobFactory()
    provider_account = ProviderAccountFactory(
        workspace_id=job.workspace_id, 
        provider_account_id=job.provider_account_id,
        provider_key=job.provider_key
    )
    
    use_case._provider_account_repository.get_by_id.return_value = provider_account
    use_case._delivery_safety_service.check_rate_limit.return_value = DeliveryRateLimitResult(
        allowed=False, violated_scope="workspace", violated_key="ws_1", limit=10, window_seconds=60
    )
    
    await use_case.execute(job)
    
    use_case._sender_registry.resolve.assert_not_called()
    use_case._delivery_job_repository.update.assert_called_once()
    
    updated_job = use_case._delivery_job_repository.update.call_args[0][0]
    assert updated_job.status == DeliveryJobStatus.PENDING
    assert "rate limit exceeded" in updated_job.last_error
    assert updated_job.next_retry_at is not None

@pytest.mark.asyncio
async def test_process_delivery_job_transient_failure(use_case):
    job = DeliveryJobFactory(retry_count=0, max_retries=3)
    provider_account = ProviderAccountFactory(
        workspace_id=job.workspace_id, 
        provider_account_id=job.provider_account_id,
        provider_key=job.provider_key
    )
    
    use_case._provider_account_repository.get_by_id.return_value = provider_account
    use_case._delivery_safety_service.check_rate_limit.return_value = DeliveryRateLimitResult(allowed=True)
    
    mock_sender = AsyncMock()
    mock_sender.send.side_effect = TimeoutError("Connection timed out")
    use_case._sender_registry.resolve.return_value = mock_sender
    
    await use_case.execute(job)
    
    use_case._delivery_job_repository.update.assert_called_once()
    updated_job = use_case._delivery_job_repository.update.call_args[0][0]
    
    assert updated_job.status == DeliveryJobStatus.PENDING
    assert updated_job.retry_count == 1
    assert "Connection timed out" in updated_job.last_error

@pytest.mark.asyncio
async def test_process_delivery_job_permanent_failure(use_case):
    job = DeliveryJobFactory(retry_count=3, max_retries=3)
    provider_account = ProviderAccountFactory(
        workspace_id=job.workspace_id, 
        provider_account_id=job.provider_account_id,
        provider_key=job.provider_key
    )
    
    use_case._provider_account_repository.get_by_id.return_value = provider_account
    use_case._delivery_safety_service.check_rate_limit.return_value = DeliveryRateLimitResult(allowed=True)
    
    mock_sender = AsyncMock()
    mock_sender.send.side_effect = TimeoutError("Connection timed out")
    use_case._sender_registry.resolve.return_value = mock_sender
    
    await use_case.execute(job)
    
    use_case._delivery_job_repository.update.assert_called_once()
    updated_job = use_case._delivery_job_repository.update.call_args[0][0]
    
    assert updated_job.status == DeliveryJobStatus.FAILED
    use_case._dead_letter_job_repository.save.assert_called_once()

@pytest.mark.asyncio
async def test_process_delivery_job_provider_account_not_found(use_case):
    job = DeliveryJobFactory()
    use_case._provider_account_repository.get_by_id.return_value = None

    await use_case.execute(job)

    use_case._dead_letter_job_repository.save.assert_called_once()
    use_case._delivery_job_repository.update.assert_called_once()
    updated_job = use_case._delivery_job_repository.update.call_args[0][0]
    assert updated_job.status.value == "FAILED"
    assert "provider account unavailable" in updated_job.last_error

@pytest.mark.asyncio
async def test_process_delivery_job_provider_account_inactive(use_case):
    job = DeliveryJobFactory()
    provider_account = ProviderAccountFactory(is_active=False)
    use_case._provider_account_repository.get_by_id.return_value = provider_account

    await use_case.execute(job)

    use_case._dead_letter_job_repository.save.assert_called_once()
    use_case._delivery_job_repository.update.assert_called_once()
    updated_job = use_case._delivery_job_repository.update.call_args[0][0]
    assert updated_job.status.value == "FAILED"
    assert "provider account unavailable" in updated_job.last_error

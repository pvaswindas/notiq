import pytest
from unittest.mock import AsyncMock
from src.bootstrap.workers.notification_worker import NotificationWorker
from tests.factories.models import DeliveryJobFactory
import logging

@pytest.fixture
def worker(mocker):
    return NotificationWorker(
        worker_id="test_worker_1",
        delivery_job_repository=AsyncMock(),
        process_delivery_job_use_case=AsyncMock(),
        metrics_service=mocker.Mock(),
        batch_size=10,
        poll_interval_seconds=0.1,
        lease_seconds=30,
    )

@pytest.mark.asyncio
async def test_worker_process_batch_success(worker):
    jobs = [DeliveryJobFactory(), DeliveryJobFactory()]
    worker._delivery_job_repository.claim_due_jobs.return_value = jobs
    
    processed_count = await worker.process_batch()
    
    assert processed_count == 2
    worker._delivery_job_repository.claim_due_jobs.assert_called_once_with(
        worker_id="test_worker_1",
        limit=10,
        lease_seconds=30
    )
    assert worker._process_delivery_job_use_case.execute.call_count == 2

@pytest.mark.asyncio
async def test_worker_survives_use_case_exception(worker, caplog):
    jobs = [DeliveryJobFactory(), DeliveryJobFactory()]
    worker._delivery_job_repository.claim_due_jobs.return_value = jobs
    
    # First job throws unhandled exception, second job succeeds
    worker._process_delivery_job_use_case.execute.side_effect = [
        RuntimeError("Catastrophic DB failure"),
        None
    ]
    
    with caplog.at_level(logging.ERROR):
        processed_count = await worker.process_batch()
        
    assert processed_count == 2
    assert worker._process_delivery_job_use_case.execute.call_count == 2
    
    # Assert exception was caught and logged without crashing loop
    assert "worker_job_unexpected_failure" in caplog.text

@pytest.mark.asyncio
async def test_worker_idle_batch(worker):
    worker._delivery_job_repository.claim_due_jobs.return_value = []
    
    processed_count = await worker.process_batch()
    
    assert processed_count == 0
    worker._process_delivery_job_use_case.execute.assert_not_called()

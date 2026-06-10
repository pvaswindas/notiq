import pytest
import unittest.mock as mock
from datetime import datetime, timezone, timedelta

from src.infrastructure.persistence.postgres.delivery_job_repository import PostgresDeliveryJobRepository
from src.modules.notifications.domain.entities.delivery_job import DeliveryJobStatus
from tests.factories.models import DeliveryJobFactory
from src.infrastructure.persistence.postgres.models import WorkspaceModel, ChannelModel, ProviderAccountModel


class MockAsyncSessionManager:
    """Correctly implements the async context manager protocol to yield the test db_session."""
    def __init__(self, db_session):
        self.db_session = db_session

    async def __aenter__(self):
        return self.db_session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


@pytest.fixture
def repo():
    return PostgresDeliveryJobRepository()


@pytest.mark.asyncio
async def test_claim_due_jobs_claims_pending(db_session, repo):
    ws_id = "ws_test_pending"
    ch_id = "ch_test_pending"
    pa_id = "pa_test_pending"

    ws = WorkspaceModel(workspace_id=ws_id, name="Test Pending", is_active=True)
    db_session.add(ws)
    await db_session.flush()

    pa = ProviderAccountModel(
        provider_account_id=pa_id,
        workspace_id=ws_id,
        provider_key="telegram",
        credentials={},
        is_active=True
    )
    db_session.add(pa)
    await db_session.flush()

    ch = ChannelModel(
        channel_id=ch_id,
        workspace_id=ws_id,
        provider_key="telegram",
        destination='{"chat_id": "123456"}',
        provider_account_id=pa_id,
        is_active=True,
        metadata_json={}
    )
    db_session.add(ch)
    await db_session.flush()

    job = DeliveryJobFactory(
        workspace_id=ws_id,
        channel_id=ch_id,
        provider_account_id=pa_id,
        status=DeliveryJobStatus.PENDING,
        next_retry_at=None
    )

    mock_cm = MockAsyncSessionManager(db_session)

    with mock.patch("src.infrastructure.persistence.postgres.delivery_job_repository.AsyncSessionLocal", return_value=mock_cm):
        await repo.save(job)
        worker_id = "test_worker_1"
        claimed = await repo.claim_due_jobs(worker_id=worker_id, limit=10, lease_seconds=30)

    assert len(claimed) == 1
    assert claimed[0].job_id == job.job_id
    assert claimed[0].status == DeliveryJobStatus.PROCESSING
    assert claimed[0].processing_owner == worker_id
    assert claimed[0].processing_expires_at is not None


@pytest.mark.asyncio
async def test_claim_due_jobs_ignores_locked(db_session, repo):
    ws_id = "ws_test_locked"
    ch_id = "ch_test_locked"
    pa_id = "pa_test_locked"

    ws = WorkspaceModel(workspace_id=ws_id, name="Test Locked", is_active=True)
    db_session.add(ws)
    await db_session.flush()

    pa = ProviderAccountModel(
        provider_account_id=pa_id,
        workspace_id=ws_id,
        provider_key="telegram",
        credentials={},
        is_active=True
    )
    db_session.add(pa)
    await db_session.flush()

    ch = ChannelModel(
        channel_id=ch_id,
        workspace_id=ws_id,
        provider_key="telegram",
        destination='{"chat_id": "123456"}',
        provider_account_id=pa_id,
        is_active=True,
        metadata_json={}
    )
    db_session.add(ch)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    future = now + timedelta(seconds=60)
    job = DeliveryJobFactory(
        workspace_id=ws_id,
        channel_id=ch_id,
        provider_account_id=pa_id,
        status=DeliveryJobStatus.PROCESSING,
        processing_owner="other_worker",
        processing_expires_at=future
    )

    mock_cm = MockAsyncSessionManager(db_session)

    with mock.patch("src.infrastructure.persistence.postgres.delivery_job_repository.AsyncSessionLocal", return_value=mock_cm):
        await repo.save(job)
        claimed = await repo.claim_due_jobs(worker_id="test_worker_1", limit=10, lease_seconds=30)

    assert len(claimed) == 0


@pytest.mark.asyncio
async def test_claim_due_jobs_claims_expired_processing(db_session, repo):
    ws_id = "ws_test_expired"
    ch_id = "ch_test_expired"
    pa_id = "pa_test_expired"

    ws = WorkspaceModel(workspace_id=ws_id, name="Test Expired", is_active=True)
    db_session.add(ws)
    await db_session.flush()

    pa = ProviderAccountModel(
        provider_account_id=pa_id,
        workspace_id=ws_id,
        provider_key="telegram",
        credentials={},
        is_active=True
    )
    db_session.add(pa)
    await db_session.flush()

    ch = ChannelModel(
        channel_id=ch_id,
        workspace_id=ws_id,
        provider_key="telegram",
        destination='{"chat_id": "123456"}',
        provider_account_id=pa_id,
        is_active=True,
        metadata_json={}
    )
    db_session.add(ch)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    past = now - timedelta(seconds=60)
    job = DeliveryJobFactory(
        workspace_id=ws_id,
        channel_id=ch_id,
        provider_account_id=pa_id,
        status=DeliveryJobStatus.PROCESSING,
        processing_owner="crashed_worker",
        processing_expires_at=past
    )

    mock_cm = MockAsyncSessionManager(db_session)

    with mock.patch("src.infrastructure.persistence.postgres.delivery_job_repository.AsyncSessionLocal", return_value=mock_cm):
        await repo.save(job)
        claimed = await repo.claim_due_jobs(worker_id="test_worker_1", limit=10, lease_seconds=30)

    assert len(claimed) == 1
    assert claimed[0].job_id == job.job_id
    assert claimed[0].processing_owner == "test_worker_1"

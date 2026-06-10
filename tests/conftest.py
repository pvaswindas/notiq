import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy import event
from unittest.mock import patch

from src.infrastructure.db.base import Base
from src.bootstrap.settings import settings

# Test DB Engine with NullPool to avoid connection sharing across tests
test_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=False,
)
TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create all tables in the test database once per session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional session that rolls back after each test."""
    async with test_engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()
        
        async_session = AsyncSession(bind=conn, expire_on_commit=False)
        
        @event.listens_for(async_session.sync_session, "after_transaction_end")
        def end_savepoint(session, transaction):
            if conn.closed:
                return
            if not conn.in_nested_transaction():
                conn.sync_connection.begin_nested()

        with patch("src.infrastructure.db.session.AsyncSessionLocal", return_value=async_session):
            yield async_session
        
        await async_session.close()
        await conn.rollback()

@pytest.fixture
def mock_container(mocker):
    """Override the ContainerFactory to return a container with mocked dependencies."""
    from src.bootstrap.container import ContainerFactory
    
    # We patch build() to intercept DI resolution.
    original_build = ContainerFactory.build
    container_patch = mocker.patch("src.bootstrap.container.ContainerFactory.build")
    container = original_build(ContainerFactory())
    container_patch.return_value = container
    return container

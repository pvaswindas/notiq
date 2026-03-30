from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.bootstrap.settings import settings


engine = create_async_engine(settings.database_url, future=True, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    """Yield an async database session for dependency-injection scenarios."""

    async with AsyncSessionLocal() as session:
        yield session

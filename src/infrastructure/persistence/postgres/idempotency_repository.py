from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from src.infrastructure.db.session import AsyncSessionLocal
from src.infrastructure.persistence.postgres.models import IdempotencyKeyModel
from src.modules.notifications.ports.idempotency_repository_port import IdempotencyRepositoryPort


class PostgresIdempotencyRepository(IdempotencyRepositoryPort):
    """Postgres adapter for atomic idempotency-key claims."""

    async def claim(self, dedupe_key: str) -> bool:
        """Insert dedupe key and return whether the claim succeeded."""

        async with AsyncSessionLocal() as session:
            model = IdempotencyKeyModel(dedupe_key=dedupe_key, created_at=datetime.now(timezone.utc))
            session.add(model)
            try:
                await session.commit()
                return True
            except IntegrityError:
                await session.rollback()
                return False

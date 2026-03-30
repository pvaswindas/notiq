from abc import ABC, abstractmethod


class IdempotencyRepositoryPort(ABC):
    """Port for atomic dedupe-key claims used by idempotent intake."""

    @abstractmethod
    async def claim(self, dedupe_key: str) -> bool:
        """Claim a dedupe key, returning False when it already exists."""

        pass

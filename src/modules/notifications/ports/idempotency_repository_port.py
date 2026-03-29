from abc import ABC, abstractmethod


class IdempotencyRepositoryPort(ABC):
    @abstractmethod
    async def claim(self, dedupe_key: str) -> bool:
        pass

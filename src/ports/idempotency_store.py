from abc import ABC, abstractmethod


class IdempotencyStorePort(ABC):
    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def save(self, key: str, ttl_seconds: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError

import asyncio

from src.modules.notifications.domain.repositories import IdempotencyRepository


class InMemoryIdempotencyRepository(IdempotencyRepository):
    """
    Purpose:
    - Provide async in-memory dedupe key storage adapter.

    Responsibilities:
    - Track seen dedupe keys for idempotent submission.

    Inputs:
    - None.

    Outputs:
    - Idempotency state operations.

    Constraints:
    - Process-local storage only.
    """

    def __init__(self) -> None:
        """
        Purpose:
        - Initialize dedupe key store.

        Responsibilities:
        - Create in-memory set for key tracking.

        Inputs:
        - None.

        Outputs:
        - None

        Constraints:
        - Data is not persisted between process restarts.
        """

        self._keys: set[str] = set()
        self._lock = asyncio.Lock()

    async def exists(self, dedupe_key: str) -> bool:
        """
        Purpose:
        - Check if a dedupe key is already registered.

        Responsibilities:
        - Read key presence from in-memory store.

        Inputs:
        - dedupe_key: str

        Outputs:
        - bool

        Constraints:
        - Must be side-effect free.
        """

        async with self._lock:
            return dedupe_key in self._keys

    async def claim(self, dedupe_key: str) -> bool:
        """
        Purpose:
        - Atomically claim dedupe key in in-memory store.

        Responsibilities:
        - Insert unseen key and report success.

        Inputs:
        - dedupe_key: str

        Outputs:
        - bool

        Constraints:
        - Must be safe under concurrent coroutines.
        """

        async with self._lock:
            if dedupe_key in self._keys:
                return False
            self._keys.add(dedupe_key)
            return True

    async def save(self, dedupe_key: str) -> None:
        """
        Purpose:
        - Register dedupe key in in-memory store.

        Responsibilities:
        - Add key without duplicate side effects.

        Inputs:
        - dedupe_key: str

        Outputs:
        - None

        Constraints:
        - Operation is idempotent.
        """

        async with self._lock:
            self._keys.add(dedupe_key)

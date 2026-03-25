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

        return dedupe_key in self._keys

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

        self._keys.add(dedupe_key)

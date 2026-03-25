from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EventFingerprint:
    """
    Purpose:
    - Represent an idempotency fingerprint for event dispatch.

    Responsibilities:
    - Provide a strongly-typed wrapper around hash values.

    Inputs:
    - value: str

    Outputs:
    - EventFingerprint value object.

    Constraints:
    - Value must be non-empty.
    """

    value: str

    def __post_init__(self) -> None:
        """
        Purpose:
        - Validate fingerprint content.

        Responsibilities:
        - Ensure value exists and is non-empty.

        Inputs:
        - None.

        Outputs:
        - None.

        Constraints:
        - Raises ValueError for empty fingerprints.
        """

        if not self.value:
            raise ValueError("event fingerprint must not be empty")

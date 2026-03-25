from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderKey:
    """
    Purpose:
    - Model a validated provider identifier.

    Responsibilities:
    - Enforce minimal invariants for provider key values.

    Inputs:
    - value: str

    Outputs:
    - ProviderKey value object.

    Constraints:
    - Value must be non-empty after trimming.
    """

    value: str

    def __post_init__(self) -> None:
        """
        Purpose:
        - Validate provider key integrity.

        Responsibilities:
        - Ensure value is not blank.

        Inputs:
        - None.

        Outputs:
        - None.

        Constraints:
        - Raises ValueError for blank values.
        """

        if not self.value.strip():
            raise ValueError("provider key must not be blank")

from abc import ABC, abstractmethod


class IdGeneratorPort(ABC):
    """
    Purpose:
    - Define identifier generation contract for application workflows.

    Responsibilities:
    - Provide unique identifier values for new domain records.

    Inputs:
    - None.

    Outputs:
    - str identifier.

    Constraints:
    - Implementations must return non-empty strings.
    """

    @abstractmethod
    def new_id(self) -> str:
        """
        Purpose:
        - Generate a new unique identifier.

        Responsibilities:
        - Return a stable string representation of a fresh identifier.

        Inputs:
        - None.

        Outputs:
        - str

        Constraints:
        - Returned value must be non-empty.
        """

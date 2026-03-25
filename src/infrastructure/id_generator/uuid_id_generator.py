import uuid

from src.modules.notifications.ports.id_generator_port import IdGeneratorPort


class UUIDIdGenerator(IdGeneratorPort):
    """
    Purpose:
    - Provide UUID4-based identifier generation for infrastructure wiring.

    Responsibilities:
    - Generate unique string identifiers.
    - Implement the application id generation port.

    Inputs:
    - None.

    Outputs:
    - str identifier values.

    Constraints:
    - Must stay stateless and deterministic in format only.
    """

    def new_id(self) -> str:
        """
        Purpose:
        - Generate a new unique identifier.

        Responsibilities:
        - Return UUID4 value as a string.

        Inputs:
        - None.

        Outputs:
        - str

        Constraints:
        - Returned value must be non-empty.
        """

        return str(uuid.uuid4())

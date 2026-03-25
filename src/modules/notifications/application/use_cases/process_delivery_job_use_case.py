from src.modules.notifications.domain.entities.delivery_job import DeliveryJob
from src.modules.notifications.ports.sender_registry_port import SenderRegistryPort


class ProcessDeliveryJobUseCase:
    """
    Purpose:
    - Orchestrate provider dispatch for a single delivery job.

    Responsibilities:
    - Resolve sender using provider key.
    - Delegate message delivery to resolved sender.

    Inputs:
    - sender_registry: SenderRegistryPort

    Outputs:
    - None

    Constraints:
    - Must not pull from queue or implement retry policy.
    """

    def __init__(self, sender_registry: SenderRegistryPort) -> None:
        """
        Purpose:
        - Construct use case dependencies.

        Responsibilities:
        - Store sender registry dependency.

        Inputs:
        - sender_registry: SenderRegistryPort

        Outputs:
        - None

        Constraints:
        - Registry must resolve provider implementations via ports.
        """

        self._sender_registry = sender_registry

    async def execute(self, job: DeliveryJob) -> None:
        """
        Purpose:
        - Process and deliver one queued job.

        Responsibilities:
        - Resolve provider sender and invoke send.

        Inputs:
        - job: DeliveryJob

        Outputs:
        - None

        Constraints:
        - Exceptions propagate to worker for retry handling.
        """

        sender = self._sender_registry.resolve(job.provider_key)
        await sender.send(job)

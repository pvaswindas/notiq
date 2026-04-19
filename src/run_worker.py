import asyncio
import logging

from src.bootstrap.container import ContainerFactory


async def main() -> None:
    """Start the modular notification worker runtime.

    This function:
    - Configures process-level logging for the worker runtime.
    - Builds the shared dependency container.
    - Starts the long-running notification worker loop.

    Returns:
        None

    Important:
    - This entrypoint contains runtime bootstrapping only.
    - Delivery policy remains in the notification application layer and worker
      orchestration components.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    container = ContainerFactory().build()
    await container.notification_worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())

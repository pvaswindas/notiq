import asyncio
import logging

from src.bootstrap.container import ContainerFactory


async def main() -> None:
    """Bootstrap dependencies and run the notification worker loop forever."""

    logging.basicConfig(level=logging.INFO)
    container = ContainerFactory().build()
    await container.notification_worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())

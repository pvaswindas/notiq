import asyncio
import logging

from src.bootstrap.container import ContainerFactory


async def main() -> None:
    """Start the modular notification worker runtime."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    container = ContainerFactory().build()
    await container.notification_worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())

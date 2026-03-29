import asyncio
import logging

from src.bootstrap.container import ContainerFactory


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    container = ContainerFactory().build()
    await container.notification_worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())

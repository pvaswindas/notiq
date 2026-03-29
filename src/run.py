import asyncio

import uvicorn

from src.bootstrap.settings import settings
from src.worker_main import main as worker_main


def run() -> None:
    if settings.app_mode == "worker":
        asyncio.run(worker_main())
        return

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()

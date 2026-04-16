import uvicorn

from src.bootstrap.settings import settings


def run() -> None:
    """Start API runtime."""

    if settings.app_mode == "worker":
        raise RuntimeError(
            "APP_MODE=worker is no longer supported. "
            "Run the modular notification worker with: python -m src.run_worker"
        )

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()

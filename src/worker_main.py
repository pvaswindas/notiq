import asyncio

async def main() -> None:
    """Legacy entrypoint retained for compatibility."""
    raise RuntimeError(
        "worker_main is deprecated. Run Celery with: "
        "celery -A src.infrastructure.celery_app.celery_app worker --loglevel=info"
    )


if __name__ == "__main__":
    asyncio.run(main())

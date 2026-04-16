import asyncio


async def main() -> None:
    """Legacy entrypoint retained as an alias for the modular worker."""
    raise RuntimeError(
        "worker_main is deprecated. Run the modular notification worker with: "
        "python -m src.run_worker"
    )


if __name__ == "__main__":
    asyncio.run(main())

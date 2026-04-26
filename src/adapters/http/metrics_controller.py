from fastapi import APIRouter

from src.shared.observability.metrics_service import MetricsService


class MetricsControllerFactory:
    """Expose a lightweight JSON metrics snapshot for monitoring hooks."""

    def __init__(self, metrics_service: MetricsService) -> None:
        self._metrics_service = metrics_service

    def build(self) -> APIRouter:
        router = APIRouter(tags=["metrics"])

        @router.get("/metrics")
        async def get_metrics() -> dict[str, int]:
            return await self._metrics_service.snapshot()

        return router


import asyncio
from contextlib import suppress

from fastapi import FastAPI

from src.adapters.http.events_router import EventRouterFactory
from src.application.services.notification_dispatcher import NotificationDispatcher
from src.bootstrap.container import ContainerFactory
from src.bootstrap.event_ingestion_container import EventIngestionContainerFactory
from src.bootstrap.workers.notification_worker import EventQueueNotificationWorker
from src.infrastructure.providers.provider_factory import ProviderFactory
from src.modules.notifications.adapters.inbound.http.routes import NotificationRouterFactory


class ApplicationFactory:
    """Build the FastAPI application with all notification routes wired in."""

    def create(self) -> FastAPI:
        container = ContainerFactory().build()
        event_ingestion_container = EventIngestionContainerFactory().build()
        app = FastAPI(title="Notiq")

        notification_router = NotificationRouterFactory(
            send_notification_use_case=container.send_notification_use_case,
        ).build()
        events_router = EventRouterFactory(
            process_event_use_case=event_ingestion_container.process_event_use_case,
        ).build()

        app.include_router(notification_router)
        app.include_router(events_router)

        provider_factory = ProviderFactory()
        dispatcher = NotificationDispatcher(provider_factory=provider_factory)
        worker = EventQueueNotificationWorker(
            event_queue=event_ingestion_container.event_queue,
            dispatcher=dispatcher,
        )

        app.state.event_queue_worker = worker
        app.state.event_queue_worker_task = None

        @app.on_event("startup")
        async def _start_event_queue_worker() -> None:
            app.state.event_queue_worker_task = asyncio.create_task(worker.run_forever())

        @app.on_event("shutdown")
        async def _stop_event_queue_worker() -> None:
            worker.shutdown()
            task = app.state.event_queue_worker_task
            if task is None:
                return
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        return app

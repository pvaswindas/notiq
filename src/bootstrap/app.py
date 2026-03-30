from fastapi import FastAPI

from src.adapters.http.events_router import EventRouterFactory
from src.bootstrap.container import ContainerFactory
from src.bootstrap.event_ingestion_container import EventIngestionContainerFactory
from src.modules.notifications.adapters.inbound.http.routes import NotificationRouterFactory


class ApplicationFactory:
    """Build the FastAPI application with all notification routes wired in."""

    def create(self) -> FastAPI:
        """Create and return the API application instance.

        Flow:
        - Builds the dependency container.
        - Creates the FastAPI app shell.
        - Registers inbound notification routes backed by use cases.
        """

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

        return app

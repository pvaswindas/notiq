from fastapi import FastAPI

from src.bootstrap.container import ContainerFactory
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
        app = FastAPI(title="Notiq")

        router = NotificationRouterFactory(
            send_notification_use_case=container.send_notification_use_case,
        ).build()
        app.include_router(router)

        return app

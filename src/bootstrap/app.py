from fastapi import FastAPI

from src.bootstrap.container import ContainerFactory
from src.modules.notifications.adapters.inbound.http.routes import NotificationRouterFactory


class ApplicationFactory:
    def create(self) -> FastAPI:
        container = ContainerFactory().build()
        app = FastAPI(title="Notiq")

        router = NotificationRouterFactory(
            send_notification_use_case=container.send_notification_use_case,
        ).build()
        app.include_router(router)

        return app

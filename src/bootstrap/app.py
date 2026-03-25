import asyncio

from fastapi import FastAPI

from src.bootstrap.container import ContainerFactory
from src.modules.notifications.adapters.inbound.http.routes import NotificationRouterFactory


class ApplicationFactory:
    """
    Purpose:
    - Build FastAPI application with fully wired dependencies.

    Responsibilities:
    - Register inbound routes.
    - Start and stop background notification worker.

    Inputs:
    - None.

    Outputs:
    - FastAPI application instance.

    Constraints:
    - Must keep domain and application layers framework-independent.
    """

    def create(self) -> FastAPI:
        """
        Purpose:
        - Create configured application instance.

        Responsibilities:
        - Build container.
        - Include notification routes.
        - Manage worker lifecycle hooks.

        Inputs:
        - None.

        Outputs:
        - FastAPI

        Constraints:
        - Background worker must run asynchronously.
        """

        container = ContainerFactory().build()
        app = FastAPI(title="Notiq")

        router = NotificationRouterFactory(
            send_notification_use_case=container.send_notification_use_case,
        ).build()
        app.include_router(router)

        @app.on_event("startup")
        async def startup_worker() -> None:
            """
            Purpose:
            - Start background notification worker.

            Responsibilities:
            - Create asynchronous worker task.

            Inputs:
            - None.

            Outputs:
            - None

            Constraints:
            - Worker execution must not block event loop startup.
            """

            app.state.worker_task = asyncio.create_task(container.notification_worker.run_forever())

        @app.on_event("shutdown")
        async def shutdown_worker() -> None:
            """
            Purpose:
            - Stop background notification worker.

            Responsibilities:
            - Cancel and await worker task.

            Inputs:
            - None.

            Outputs:
            - None

            Constraints:
            - Cancellation must be handled gracefully.
            """

            worker_task = app.state.worker_task
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass

        return app

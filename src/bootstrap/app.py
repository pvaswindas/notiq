from fastapi import FastAPI

from src.adapters.http.channel_controller import ChannelControllerFactory
from src.adapters.http.events_router import EventRouterFactory
from src.adapters.http.workspace_controller import WorkspaceControllerFactory
from src.bootstrap.container import ContainerFactory
from src.bootstrap.event_ingestion_container import EventIngestionContainerFactory
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
        workspace_router = WorkspaceControllerFactory(
            create_workspace_use_case=container.create_workspace_use_case,
            get_workspace_use_case=container.get_workspace_use_case,
            list_workspaces_use_case=container.list_workspaces_use_case,
        ).build()
        channel_router = ChannelControllerFactory(
            create_channel_use_case=container.create_channel_use_case,
            list_channels_use_case=container.list_channels_use_case,
            update_channel_use_case=container.update_channel_use_case,
            disable_channel_use_case=container.disable_channel_use_case,
        ).build()

        app.include_router(notification_router)
        app.include_router(events_router)
        app.include_router(workspace_router)
        app.include_router(channel_router)

        return app

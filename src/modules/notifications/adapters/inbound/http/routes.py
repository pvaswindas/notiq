from fastapi import APIRouter

from src.modules.notifications.adapters.inbound.http.schemas import SendNotificationRequest, SendNotificationResponse
from src.modules.notifications.application.dto.send_notification_command import SendNotificationCommand
from src.modules.notifications.application.use_cases.send_notification_use_case import SendNotificationUseCase


class NotificationRouterFactory:
    def __init__(self, send_notification_use_case: SendNotificationUseCase) -> None:
        self._send_notification_use_case = send_notification_use_case

    def build(self) -> APIRouter:
        router = APIRouter(prefix="/notifications", tags=["notifications"])

        @router.post("/send", response_model=SendNotificationResponse)
        async def send_notification(request: SendNotificationRequest) -> SendNotificationResponse:
            command = SendNotificationCommand(
                workspace_id=request.workspace_id,
                event_id=request.event_id,
                event_name=request.event_name,
                payload=request.payload,
                channel_ids=request.channel_ids,
            )
            result = await self._send_notification_use_case.execute(command)
            return SendNotificationResponse(
                enqueued_jobs=result.enqueued_jobs,
                skipped_duplicates=result.skipped_duplicates,
            )

        return router

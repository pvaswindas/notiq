from fastapi import APIRouter

from src.modules.notifications.adapters.inbound.http.schemas import (
    SendNotificationRequest,
    SendNotificationResponse,
)
from src.modules.notifications.application.dto.send_notification_command import SendNotificationCommand
from src.modules.notifications.application.use_cases.send_notification_use_case import SendNotificationUseCase


class NotificationRouterFactory:
    """
    Purpose:
    - Build HTTP router for notification submission endpoints.

    Responsibilities:
    - Map request models to use case commands.
    - Return response models from use case outputs.

    Inputs:
    - send_notification_use_case: SendNotificationUseCase

    Outputs:
    - APIRouter

    Constraints:
    - Must keep business logic out of routes.
    """

    def __init__(self, send_notification_use_case: SendNotificationUseCase) -> None:
        """
        Purpose:
        - Initialize router factory with required use case.

        Responsibilities:
        - Store use case dependency for endpoint orchestration.

        Inputs:
        - send_notification_use_case: SendNotificationUseCase

        Outputs:
        - None

        Constraints:
        - Use case must encapsulate business rules.
        """

        self._send_notification_use_case = send_notification_use_case

    def build(self) -> APIRouter:
        """
        Purpose:
        - Create and configure notification HTTP router.

        Responsibilities:
        - Register endpoint handlers and response models.

        Inputs:
        - None.

        Outputs:
        - APIRouter

        Constraints:
        - Endpoints must remain thin orchestration layers.
        """

        router = APIRouter(prefix="/notifications", tags=["notifications"])

        @router.post("/send", response_model=SendNotificationResponse)
        async def send_notification(request: SendNotificationRequest) -> SendNotificationResponse:
            """
            Purpose:
            - Handle notification submission requests.

            Responsibilities:
            - Convert inbound schema to application command.
            - Invoke use case and map result to response schema.

            Inputs:
            - request: SendNotificationRequest

            Outputs:
            - SendNotificationResponse

            Constraints:
            - Must not include business rules or provider logic.
            """

            command = SendNotificationCommand(
                workspace_id=request.workspace_id,
                event_id=request.event_id,
                event_name=request.event_name,
                payload=request.payload,
            )
            result = await self._send_notification_use_case.execute(command)
            return SendNotificationResponse(
                enqueued_jobs=result.enqueued_jobs,
                skipped_duplicates=result.skipped_duplicates,
            )

        return router

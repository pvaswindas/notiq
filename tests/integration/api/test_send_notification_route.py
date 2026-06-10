import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from src.modules.notifications.application.dto.queued_delivery_dto import QueuedDeliveryResultDTO
from src.bootstrap.app import ApplicationFactory


@pytest.mark.asyncio
async def test_send_notification_api_success():
    mock_use_case = AsyncMock()
    mock_use_case.execute.return_value = QueuedDeliveryResultDTO(
        enqueued_jobs=2,
        skipped_duplicates=0
    )

    with patch("src.bootstrap.container.ContainerFactory.build") as mock_build:
        mock_container = mock_build.return_value
        mock_container.send_notification_use_case = mock_use_case

        test_app = ApplicationFactory().create()

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post("/notifications/send", json={
                "workspace_id": "ws_123",
                "event_id": "evt_456",
                "event_name": "user.signup",
                "payload": {"user_id": "1"}
            })

    assert response.status_code == 200
    assert response.json() == {
        "enqueued_jobs": 2,
        "skipped_duplicates": 0
    }


@pytest.mark.asyncio
async def test_send_notification_api_validation_error():
    test_app = ApplicationFactory().create()
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.post("/notifications/send", json={
            "workspace_id": "ws_123",
            "payload": {}
        })

    assert response.status_code == 422
    assert "detail" in response.json()

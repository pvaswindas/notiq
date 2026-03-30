# Send Notification API

## 1. Endpoint
- Method: `POST`
- Path: `/notifications/send`
- Handler: `NotificationRouterFactory.send_notification`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization` is not enforced by current implementation.

## 3. Request Payload

```json
{
  "workspace_id": "workspace-1",
  "event_id": "evt-1001",
  "event_name": "order.created",
  "payload": {
    "order_id": "ORD-42",
    "total": 1999
  },
  "channel_ids": ["ch-telegram-1", "ch-email-2"]
}
```

### Field-by-field explanation
- `workspace_id` (`string`, required): Tenant identifier used for workspace validation and channel lookup.
- `event_id` (`string`, required): Stable event identifier used as part of idempotency fingerprinting.
- `event_name` (`string`, required): Business event type used in message mapping.
- `payload` (`object`, optional, default `{}`): Arbitrary event body passed to message mapping.
- `channel_ids` (`array<string> | null`, optional): Restricts fan-out to selected active channels.

## 4. Response
### Success (`200 OK`)

```json
{
  "enqueued_jobs": 2,
  "skipped_duplicates": 1
}
```

Fields:
- `enqueued_jobs`: Number of newly persisted delivery jobs.
- `skipped_duplicates`: Number of channel routes skipped because idempotency key was already claimed.

### Error responses
- `422 Unprocessable Entity`: Request validation failed at FastAPI/Pydantic boundary.
- `500 Internal Server Error`: Use-case/runtime exception (for example missing workspace, inactive workspace, missing provider account).

## 5. Internal Processing Flow
1. Validate payload schema.
2. Convert request to `SendNotificationCommand`.
3. Validate required identifiers.
4. Load workspace and verify active state.
5. Load active channels and apply optional `channel_ids` filter.
6. Resolve provider account per channel (explicit -> workspace default -> system default).
7. Generate idempotency key per channel and attempt atomic claim.
8. Skip duplicates, persist new `DeliveryJob` records for successful claims.
9. Return enqueue summary.

## 6. What To Do Next
- Treat success as queue acceptance, not provider delivery confirmation.
- Monitor worker execution path for eventual status transitions (`SUCCESS`/`FAILED`).
- Reuse the same `event_id` and payload on client retries to preserve idempotency behavior.

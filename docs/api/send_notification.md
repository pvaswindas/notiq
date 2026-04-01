# Send Notification API

## 1. Endpoint and Method
- Method: `POST`
- Path: `/notifications/send`
- Handler: `NotificationRouterFactory.send_notification`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization`: not required by current route implementation.

## 3. Request Payload

### Schema
- `workspace_id` (`string`, required): Workspace identifier used for workspace and channel resolution.
- `event_id` (`string`, required): Stable upstream event identifier used in idempotency fingerprint.
- `event_name` (`string`, required): Domain event name used in message construction.
- `payload` (`object`, optional, default `{}`): Arbitrary event data forwarded into message mapping.
- `channel_ids` (`array<string> | null`, optional): Limits fan-out to selected channel IDs.

### Example Request JSON
```json
{
  "workspace_id": "ws_abc123",
  "event_id": "evt_1001",
  "event_name": "order.created",
  "payload": {
    "order_id": "ORD-42",
    "amount": 1999
  },
  "channel_ids": ["chn_telegram_1", "chn_email_1"]
}
```

## 4. Response
### Success (`200 OK`)
- `enqueued_jobs` (`integer`): Count of newly persisted jobs.
- `skipped_duplicates` (`integer`): Count of channels skipped due to dedupe collision.

### Example Success Response JSON
```json
{
  "enqueued_jobs": 2,
  "skipped_duplicates": 1
}
```

### Error Responses
- `422 Unprocessable Entity`: Invalid request shape or missing required fields.
- `500 Internal Server Error`: Uncaught use-case/runtime exceptions (including workspace/account resolution failures).

## 5. Internal Processing Flow After Request
1. Validate request schema.
2. Map payload into `SendNotificationCommand`.
3. Validate required identifiers.
4. Load and validate workspace state.
5. Load active channels and apply optional channel filter.
6. Resolve provider account for each channel.
7. Compute and claim channel-scoped dedupe key.
8. Persist `DeliveryJob` for successful claims.
9. Return enqueue summary.

## 6. What To Do Next
- Treat success as accepted/queued semantics.
- Monitor asynchronous processing for terminal outcomes.
- Reuse the same `event_id` on retries to preserve dedupe behavior.

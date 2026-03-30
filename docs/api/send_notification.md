# Send Notification API

## Endpoint
- Method: `POST`
- Path: `/notifications/send`

## Headers
- `Content-Type: application/json` (required)
- `Authorization`: not currently required by implementation (add at gateway/app layer when auth is introduced)

## Request Body
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

### Fields
- `workspace_id` (`string`, required): Tenant identifier; must reference an active workspace.
- `event_id` (`string`, required): Event identity for dedupe fingerprinting.
- `event_name` (`string`, required): Logical event type.
- `payload` (`object`, optional, default `{}`): Event payload mapped into outgoing message text.
- `channel_ids` (`string[]`, optional): Restricts routing to selected channels. If omitted, all active workspace channels are considered.

## Success Response
Status: `200 OK`

```json
{
  "enqueued_jobs": 2,
  "skipped_duplicates": 1
}
```

### Response fields
- `enqueued_jobs`: Number of new delivery jobs persisted.
- `skipped_duplicates`: Number of channels skipped due to existing dedupe key.

## Error Responses
### Validation error (FastAPI/Pydantic)
Status: `422 Unprocessable Entity`

### Business validation errors from use case
Status: `500 Internal Server Error` by default in current implementation, with messages such as:
- `workspace not found: <workspace_id>`
- `workspace is inactive: <workspace_id>`
- `missing default provider account for provider=<provider_key>`

Note: mapping domain errors to structured `4xx` responses is a recommended improvement.

## Flow Guidance (What Happens After Call)
1. Request is mapped into `SendNotificationCommand`.
2. Workspace is validated.
3. Active channels are loaded and optionally filtered by `channel_ids`.
4. Provider account is resolved per channel (explicit -> workspace default -> system default).
5. Dedupe key is claimed for each channel.
6. Delivery jobs are saved in Postgres as `PENDING`.
7. Background worker eventually delivers jobs and updates status.

## What Client Should Do Next
- Treat `200` as "accepted and queued", not immediate provider delivery success.
- Store `event_id` deterministically if client-side retries are possible.
- Use `channel_ids` when targeting specific channels (for selective fan-out).
- If retrying the same event intentionally, reuse identical `event_id` and payload to leverage idempotency behavior.

# Ingest Event API (Legacy Compatibility)

## 1. Endpoint
- Method: `POST`
- Path: `/events`
- Handler: `EventRouterFactory.ingest_event`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization` is not enforced by current implementation.

## 3. Request Payload

```json
{
  "workspace_id": "workspace-1",
  "event_type": "user.created",
  "payload": {
    "user_id": "U-100"
  }
}
```

### Field-by-field explanation
- `workspace_id` (`string`, required): Tenant context for channel lookup.
- `event_type` (`string`, required): Event type name used by legacy provider pipeline.
- `payload` (`object`, optional, default `{}`): Event body forwarded to Celery task fan-out.

## 4. Response
### Success (`200 OK`)

```json
{
  "status": "accepted"
}
```

### Error responses
- `400 Bad Request`: `ValueError` raised during event/use-case validation.
- `500 Internal Server Error`: Unexpected internal processing failure.

## 5. Internal Processing Flow
1. Validate request payload.
2. Build legacy domain `Event` entity.
3. Load active channels via legacy `ChannelRepositoryPort` implementation.
4. Enqueue one Celery task per `(event, channel)` pair.
5. Return accepted response.

## 6. What To Do Next
- Treat this endpoint as compatibility flow.
- For new feature work, prefer `POST /notifications/send` and the modular notifications architecture.

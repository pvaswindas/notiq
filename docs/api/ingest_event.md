# Ingest Event API (Legacy Compatibility)

## 1. Endpoint and Method
- Method: `POST`
- Path: `/events`
- Handler: `EventRouterFactory.ingest_event`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization: Bearer <api_key>` (required)

## 3. Request Payload

### Schema
- `event_type` (`string`, required): Legacy event name used for compatibility fan-out.
- `payload` (`object`, optional, default `{}`): Event data forwarded to Celery task payload.

Workspace identity is not accepted in the body; it is derived from the authenticated API key.

### Example Request JSON
```json
{
  "event_type": "user.created",
  "payload": {
    "user_id": "U-100",
    "source": "billing-service"
  }
}
```

## 4. Response
### Success (`200 OK`)
```json
{
  "status": "accepted"
}
```

### Error Responses
- `401 Unauthorized`: Missing or malformed authorization header.
- `403 Forbidden`: Invalid or disabled API key.
- `400 Bad Request`: Input rejected by compatibility use-case validation.
- `500 Internal Server Error`: Unexpected processing failure.

## 5. Internal Processing Flow After Request
1. Validate auth header and authenticate API key.
2. Resolve workspace context from authenticated principal.
3. Validate request payload.
4. Construct legacy `Event` object with authenticated workspace ID.
5. Execute compatibility `ProcessEventUseCase`.
6. Fan out active channels into Celery task queue.
7. Return accepted response.

## 6. What To Do Next
- Treat this endpoint as compatibility-only.
- Use `/notifications/send` for new architecture investments.
- Tune compatibility Redis/celery capacity when backlog grows.

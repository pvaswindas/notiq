# Disable Channel API

## 1. Endpoint and Method
- Method: `PATCH`
- Path: `/channels/{channel_id}`
- Handler: `ChannelControllerFactory.disable_channel`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization: Bearer <api_key>` (required)

## 3. Request Payload
### Path Parameter
- `channel_id` (`string`, required): Channel identifier.

### Body Schema
- `workspace_id` (`string`, required): Ownership scope for the disable operation.

### Example Request JSON
```json
{
  "workspace_id": "ws_abc123"
}
```

## 4. Response
### Success (`200 OK`)
```json
{
  "id": "ch_5a5f6e7e7d4f4eb4b8d4a5d7",
  "workspace_id": "ws_abc123",
  "provider": "telegram",
  "provider_account_id": "pa_telegram_ops",
  "destination": "-1001234567890",
  "metadata": {
    "purpose": "ops-alerts"
  },
  "is_active": false,
  "created_at": "2026-04-16T10:15:00+00:00"
}
```

### Error Responses
- `400 Bad Request`: Invalid identifiers.
- `403 Forbidden`: Authenticated API key does not belong to `workspace_id`.
- `404 Not Found`: Channel not found for workspace scope.
- `422 Unprocessable Entity`: Request schema invalid.

## 5. Internal Processing Flow After Request
1. Validate request schema.
2. Enforce that the request workspace matches the authenticated API key workspace.
3. `DisableManagedChannelUseCase` loads the channel within the workspace scope.
4. If active, persist the channel with `is_active=false`.
5. Audit metadata is recorded for the state transition.
6. Return the updated channel representation.

## 6. What To Do Next
- Verify disabled channels no longer appear in active routing for `SendNotificationUseCase`.
- If a replacement route is needed, create a new channel with the correct provider account or destination.

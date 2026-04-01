# Disable Channel API

## 1. Endpoint and Method
- Method: `PATCH`
- Path: `/channels/{channel_id}/disable`
- Handler: `ChannelControllerFactory.disable_channel`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization`: not required by current route implementation.

## 3. Request Payload

### Path Parameter
- `channel_id` (`string`, required): Channel identifier.

### Body Schema
- `workspace_id` (`string`, required): Ownership scope for the disable operation.

### Example Request JSON
```json
{
  "workspace_id": "ws_f47ac10b58cc4372a5670e02"
}
```

## 4. Response
### Success (`200 OK`)
```json
{
  "id": "ch_5a5f6e7e7d4f4eb4b8d4a5d7",
  "workspace_id": "ws_f47ac10b58cc4372a5670e02",
  "provider": "telegram",
  "config": {
    "chat_id": "67890"
  },
  "group": "priority-medium",
  "is_active": false
}
```

### Error Responses
- `400 Bad Request`: Invalid identifiers.
- `404 Not Found`: Channel not found for workspace scope.
- `422 Unprocessable Entity`: Request schema invalid.

## 5. Internal Processing Flow After Request
1. Validate request schema.
2. Load channel by `(channel_id, workspace_id)`.
3. Return current channel unchanged if already disabled.
4. Otherwise persist channel with `is_active=false`.
5. Return channel representation.

## 6. What To Do Next
- Verify disabled channel no longer receives new fan-out jobs.
- Re-enable later using full update endpoint with `is_active=true`.

# Update Channel API

## 1. Endpoint and Method
- Method: `PUT`
- Path: `/channels/{channel_id}`
- Handler: `ChannelControllerFactory.update_channel`

## 2. Headers
- `Content-Type: application/json` (required)
- `Authorization`: not required by current route implementation.

## 3. Request Payload

### Path Parameter
- `channel_id` (`string`, required): Channel identifier.

### Body Schema
- `workspace_id` (`string`, required): Ownership check scope.
- `provider` (`string`, required): Provider key.
- `config` (`object`, optional, default `{}`): Replaces persisted config.
- `group` (`string | null`, optional): Optional grouping key.
- `is_active` (`boolean`, optional, default `true`): Desired active state.

### Example Request JSON
```json
{
  "workspace_id": "ws_f47ac10b58cc4372a5670e02",
  "provider": "telegram",
  "config": {
    "chat_id": "67890"
  },
  "group": "priority-medium",
  "is_active": true
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
  "is_active": true
}
```

### Error Responses
- `400 Bad Request`: Invalid required fields.
- `404 Not Found`: Channel not found for provided workspace.
- `422 Unprocessable Entity`: Request schema invalid.

## 5. Internal Processing Flow After Request
1. Validate request schema.
2. Normalize channel/workspace/provider identifiers.
3. Load current channel by `(channel_id, workspace_id)`.
4. Create updated channel projection.
5. Persist and return updated representation.

## 6. What To Do Next
- Use disable endpoint for soft deactivation.
- Confirm downstream routing behavior with list/send flows.
